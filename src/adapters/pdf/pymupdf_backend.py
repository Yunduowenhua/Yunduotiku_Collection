import pymupdf as fitz
from typing import List
from src.domain.geometry import CanonicalRect, TextBlock
from src.adapters.pdf.backend import PDFBackend, PDFPageInfo

class PyMuPDFPageInfo(PDFPageInfo):
    def __init__(self, page: fitz.Page, page_num: int):
        self._page = page
        self._page_num = page_num

    @property
    def page_num(self) -> int:
        return self._page_num

    @property
    def width(self) -> float:
        return self._page.rect.width

    @property
    def height(self) -> float:
        return self._page.rect.height

    def get_text_blocks(self) -> List[TextBlock]:
        blocks = self._page.get_text("blocks")
        result = []
        for b in blocks:
            if b[6] == 0:
                rect = CanonicalRect(x0=b[0], y0=b[1], x1=b[2], y1=b[3])
                result.append(TextBlock(rect=rect, text=b[4], block_type=0))
        return result
        
    def get_drawings_and_images_rects(self) -> List[CanonicalRect]:
        rects = []
        for d in self._page.get_drawings():
            r = d["rect"]
            rects.append(CanonicalRect(x0=r.x0, y0=r.y0, x1=r.x1, y1=r.y1))
            
        for img in self._page.get_images():
            r_list = self._page.get_image_rects(img[0])
            for r in r_list:
                rects.append(CanonicalRect(x0=r.x0, y0=r.y0, x1=r.x1, y1=r.y1))
        return rects

    def render_to_image(self, dpi: int = 150) -> bytes:
        pix = self._page.get_pixmap(dpi=dpi)
        return pix.tobytes("png")

    def render_rect_to_image(self, rect: CanonicalRect, dpi: int = 150) -> bytes:
        fitz_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
        pix = self._page.get_pixmap(dpi=dpi, clip=fitz_rect)
        return pix.tobytes("png")


class PyMuPDFBackend(PDFBackend):
    def __init__(self):
        self._doc = None

    def load(self, file_path: str) -> None:
        if self._doc:
            self.close()
        self._doc = fitz.open(file_path)

    def get_page_count(self) -> int:
        if not self._doc:
            raise RuntimeError("PDF is not loaded")
        return len(self._doc)

    def get_page(self, page_num: int) -> PDFPageInfo:
        if not self._doc:
            raise RuntimeError("PDF is not loaded")
        return PyMuPDFPageInfo(self._doc[page_num], page_num)

    def close(self) -> None:
        if self._doc:
            self._doc.close()
            self._doc = None
