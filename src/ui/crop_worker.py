from PySide6.QtCore import QThread, Signal
from src.adapters.pdf.pymupdf_backend import PyMuPDFBackend
from src.services.ocr_engine import RapidOCREngine
from src.services.image_preprocessor import ImagePreprocessor
from src.adapters.repositories import QuestionRepository
from src.domain.state_models import QuestionState, QuestionStatus
from src.domain.geometry import CanonicalRect
import fitz
import sqlite3
import os

class CropWorker(QThread):
    progress = Signal(str)
    crop_finished = Signal(str, str, bytes) # q_id, text, img_bytes
    error = Signal(str)

    def __init__(self, pdf_path: str, page_num: int, job_id: str, question_no: str, q_id: str, crop_bbox: tuple):
        super().__init__()
        self.pdf_path = pdf_path
        self.page_num = page_num
        self.job_id = job_id
        self.question_no = question_no
        self.q_id = q_id
        self.crop_bbox = crop_bbox # (x0, y0, x1, y1) in 72 dpi points

    def run(self):
        try:
            self.progress.emit(f"开始对第 {self.page_num+1} 页划框区域实施高精重新识别...")
            
            backend = PyMuPDFBackend()
            backend.load(self.pdf_path)
            page_info = backend.get_page(self.page_num)
            
            rect = CanonicalRect(*self.crop_bbox)
            img_bytes = page_info.render_rect_to_image(rect, dpi=200)
            backend.close()
            
            preprocessor = ImagePreprocessor()
            preprocessed_bytes = preprocessor.process(img_bytes)
            
            engine = RapidOCREngine()
            ocr_blocks = engine.recognize(preprocessed_bytes)
            extracted_text = "\n".join([b.text for b in ocr_blocks]) if ocr_blocks else ""
            
            os.makedirs("dist/output_images", exist_ok=True)
            img_path = f"dist/output_images/{self.q_id}_manual.png"
            with open(img_path, "wb") as f:
                f.write(img_bytes)
                
            conn = sqlite3.connect("tiku.db")
            conn.row_factory = sqlite3.Row
            repo = QuestionRepository(conn)
            
            q_state = repo.get_by_id(self.q_id)
            if not q_state:
                q_state = QuestionState(
                    q_id=self.q_id,
                    question_text=extracted_text,
                    image_path=img_path,
                    status=QuestionStatus.CORRECT,
                    confirmed=True,
                    manual_edited=True
                )
            else:
                q_state.question_text = extracted_text
                q_state.image_path = img_path
                q_state.confirmed = True
                q_state.manual_edited = True
                
            repo.upsert(q_state, self.job_id, self.page_num, self.question_no)
            conn.close()
            
            self.crop_finished.emit(self.q_id, extracted_text, img_bytes)
            
        except Exception as e:
            self.error.emit(str(e))
