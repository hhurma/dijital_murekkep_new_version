import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from typing import Dict, Optional

from PyQt6.QtGui import QImage

try:  # PyMuPDF is the preferred backend for rasterizing PDF pages
    import fitz  # type: ignore
except ImportError:  # pragma: no cover - library might not be available at runtime
    fitz = None


@dataclass
class PdfBackgroundLayer:
    """Model object that keeps track of a PDF background source."""

    source_path: str
    page_count: int
    dpi: int = 150
    cache_dir: Optional[str] = None
    current_page: int = 0
    _page_cache: Dict[int, QImage] = field(default_factory=dict, init=False, repr=False)
    _page_paths: Dict[int, str] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.cache_dir is None:
            base_cache = os.path.join(tempfile.gettempdir(), "dijital_murekkep_pdf_cache")
            os.makedirs(base_cache, exist_ok=True)
            identifier = hashlib.md5(self.source_path.encode("utf-8")).hexdigest()
            self.cache_dir = os.path.join(base_cache, identifier)
        os.makedirs(self.cache_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Helper properties
    # ------------------------------------------------------------------
    def has_document(self) -> bool:
        return os.path.exists(self.source_path) and self.page_count > 0

    def get_current_page_size(self):
        image = self.get_current_page_image()
        if image.isNull():
            return None
        return image.size()

    # ------------------------------------------------------------------
    # Page navigation helpers
    # ------------------------------------------------------------------
    def set_current_page(self, index: int) -> bool:
        if 0 <= index < self.page_count:
            if self.current_page != index:
                self.current_page = index
            return True
        return False

    def next_page(self) -> bool:
        return self.set_current_page(self.current_page + 1)

    def previous_page(self) -> bool:
        return self.set_current_page(self.current_page - 1)

    # ------------------------------------------------------------------
    # DPI handling
    # ------------------------------------------------------------------
    def set_dpi(self, dpi: int) -> bool:
        dpi = int(dpi)
        if dpi <= 0:
            return False
        if dpi == self.dpi:
            return False
        self.dpi = dpi
        self.clear_cache()
        return True

    def clear_cache(self) -> None:
        for path in list(self._page_paths.values()):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        self._page_cache.clear()
        self._page_paths.clear()

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def get_current_page_image(self) -> QImage:
        return self.get_page_image(self.current_page)

    def get_page_image(self, index: int) -> QImage:
        if index in self._page_cache:
            return self._page_cache[index]

        cached = self._page_paths.get(index)
        image = QImage()
        if cached and os.path.exists(cached):
            image.load(cached)
            self._page_cache[index] = image
            return image

        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) kütüphanesi yüklü değil. PDF sayfaları rasterize edilemiyor.")

        if not self.has_document():
            return image

        with fitz.open(self.source_path) as document:
            if index < 0 or index >= document.page_count:
                return image
            page = document.load_page(index)
            scale = self.dpi / 72.0
            matrix = fitz.Matrix(scale, scale)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_bytes = pixmap.tobytes("png")

        page_path = os.path.join(self.cache_dir, f"page_{index + 1}_{self.dpi}dpi.png")
        try:
            with open(page_path, "wb") as handle:
                handle.write(image_bytes)
        except OSError:
            # Fall back to an in-memory image if writing fails
            page_path = ""

        if image.loadFromData(image_bytes):
            self._page_cache[index] = image
            if page_path:
                self._page_paths[index] = page_path
        else:
            # Image load failed, ensure cache entry removed
            if page_path and os.path.exists(page_path):
                try:
                    os.remove(page_path)
                except OSError:
                    pass

        return image


class PDFImporter:
    """Utility responsible for turning PDF pages into QImage instances."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "dijital_murekkep_pdf_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def load_pdf(self, file_path: str, dpi: int = 150) -> Optional[PdfBackgroundLayer]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) kütüphanesi bulunamadı. Lütfen kurulumu tamamlayın.")

        with fitz.open(file_path) as document:
            page_count = document.page_count

        if page_count == 0:
            raise ValueError("Seçilen PDF dosyası boş görünüyor.")

        layer = PdfBackgroundLayer(
            source_path=file_path,
            page_count=page_count,
            dpi=dpi,
            cache_dir=os.path.join(self.cache_dir, hashlib.md5(file_path.encode("utf-8")).hexdigest())
        )

        # İlk sayfayı önbelleğe al - kullanıcıya daha hızlı dönüş
        layer.get_current_page_image()
        return layer
