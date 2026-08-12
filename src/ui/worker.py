from PySide6.QtCore import QThread, Signal
from src.adapters.pdf.pymupdf_backend import PyMuPDFBackend
from src.domain.column_detector import ColumnDetector
from src.domain.anchor_extractor import AnchorExtractor
from src.domain.region_planner import RegionPlanner
from src.services.ocr_engine import RapidOCREngine
from src.services.image_preprocessor import ImagePreprocessor
from src.adapters.repositories import QuestionRepository
from src.domain.state_models import QuestionState, QuestionStatus
import sqlite3
import os
import uuid

class ParseWorker(QThread):
    progress = Signal(str)
    question_found = Signal(str, str, bytes, str, int, str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, pdf_path: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.job_id = f"job_{uuid.uuid4().hex[:8]}"

    def run(self):
        try:
            self.progress.emit("初始化 PDF 引擎与数据库连接...")
            backend = PyMuPDFBackend()
            backend.load(self.pdf_path)
            total_pages = backend.get_page_count()
            
            conn = sqlite3.connect("tiku.db")
            conn.row_factory = sqlite3.Row
            repo = QuestionRepository(conn)
            
            column_detector = ColumnDetector()
            anchor_extractor = AnchorExtractor()
            region_planner = RegionPlanner()
            preprocessor = ImagePreprocessor()
            ocr_engine = RapidOCREngine()
            
            os.makedirs("dist/output_images", exist_ok=True)
            
            for page_num in range(total_pages):
                self.progress.emit(f"正在解析第 {page_num+1}/{total_pages} 页...")
                page_info = backend.get_page(page_num)
                
                text_blocks = page_info.get_text_blocks()
                if column_detector.is_multi_column(text_blocks):
                    self.progress.emit(f"警告：第 {page_num+1} 页疑似双栏版面，自动跳过以待人工复核。")
                    continue
                    
                full_text = "\n".join([b.text for b in text_blocks])
                if len(full_text.strip()) < 50:
                    page_img_bytes = page_info.render_to_image(dpi=150)
                    prep_bytes = preprocessor.process(page_img_bytes)
                    ocr_blocks = ocr_engine.recognize(prep_bytes)
                    text_blocks = ocr_blocks
                    
                anchors = anchor_extractor.extract_anchors(text_blocks)
                question_anchors = [a for a in anchors if a.anchor_type == "question"]
                
                if not question_anchors:
                    continue
                    
                other_rects = page_info.get_drawings_and_images_rects()
                
                for idx, q_anchor in enumerate(question_anchors):
                    next_anchor_y = question_anchors[idx+1].rect.y0 if idx+1 < len(question_anchors) else None
                    q_region = region_planner.plan_question_region(
                        q_anchor, text_blocks, other_rects, next_anchor_y, page_info.height
                    )
                    
                    img_bytes = page_info.render_rect_to_image(q_region.bbox, dpi=150)
                    
                    q_no = q_anchor.value
                    q_id = f"Q_{page_num+1}_{q_no}"
                    img_path = f"dist/output_images/{q_id}.png"
                    
                    with open(img_path, "wb") as f:
                        f.write(img_bytes)
                        
                    q_state = QuestionState(
                        q_id=q_id,
                        question_text=q_region.text,
                        image_path=img_path,
                        status=QuestionStatus.CORRECT if q_region.text else QuestionStatus.UNCERTAIN
                    )
                    
                    repo.upsert(q_state, self.job_id, page_num, q_no)
                    self.question_found.emit(q_id, q_region.text, img_bytes, self.job_id, page_num, q_no)
                    
            backend.close()
            conn.close()
            self.progress.emit("整本 PDF 解析完毕！")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
