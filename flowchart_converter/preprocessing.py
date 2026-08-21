"""Leitura de imagens e rasterização de páginas PDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True, slots=True)
class PageImage:
    number: int
    image: np.ndarray


def load_pages(path: Path | str, dpi: int = 200) -> list[PageImage]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {path}")
    if dpi < 72:
        raise ValueError("O DPI deve ser pelo menos 72.")

    if path.suffix.lower() == ".pdf":
        return _load_pdf(path, dpi)

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Formato de imagem inválido ou não suportado: {path}")
    return [PageImage(number=1, image=image)]


def _load_pdf(path: Path, dpi: int) -> list[PageImage]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "O suporte a PDF requer PyMuPDF. Execute: pip install -e \".[pdf]\""
        ) from exc

    pages: list[PageImage] = []
    scale = dpi / 72
    with fitz.open(path) as document:
        if document.page_count == 0:
            raise ValueError(f"O PDF não contém páginas: {path}")
        for index, page in enumerate(document):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                pixmap.height, pixmap.width, pixmap.n
            )
            if pixmap.n == 4:
                array = cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)
            else:
                array = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
            pages.append(PageImage(number=index + 1, image=array))
    return pages
