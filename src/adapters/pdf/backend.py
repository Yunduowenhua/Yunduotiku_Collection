from abc import ABC, abstractmethod
from typing import List
from src.domain.geometry import CanonicalRect, TextBlock

class PDFPageInfo(ABC):
    @property
    @abstractmethod
    def page_num(self) -> int:
        pass

    @property
    @abstractmethod
    def width(self) -> float:
        pass

    @property
    @abstractmethod
    def height(self) -> float:
        pass

    @abstractmethod
    def get_text_blocks(self) -> List[TextBlock]:
        pass

    @abstractmethod
    def get_drawings_and_images_rects(self) -> List[CanonicalRect]:
        pass

    @abstractmethod
    def render_to_image(self, dpi: int = 150) -> bytes:
        pass

    @abstractmethod
    def render_rect_to_image(self, rect: CanonicalRect, dpi: int = 150) -> bytes:
        pass


class PDFBackend(ABC):
    @abstractmethod
    def load(self, file_path: str) -> None:
        pass

    @abstractmethod
    def get_page_count(self) -> int:
        pass

    @abstractmethod
    def get_page(self, page_num: int) -> PDFPageInfo:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
