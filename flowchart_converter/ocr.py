"""Extração de texto no interior das formas detectadas."""

from __future__ import annotations

from typing import Protocol

import cv2
import numpy as np

from .models import BBox


class OcrEngine(Protocol):
    def read(self, image: np.ndarray, bbox: BBox) -> str: ...


class TesseractOcr:
    def __init__(self, language: str = "por", executable: str | None = None) -> None:
        try:
            import pytesseract
        except ImportError as exc:
            raise RuntimeError(
                "pytesseract não está instalado. Execute: pip install -e \".[ocr]\""
            ) from exc

        if executable:
            pytesseract.pytesseract.tesseract_cmd = executable
        self._pytesseract = pytesseract
        self._language = language

    def read(self, image: np.ndarray, bbox: BBox) -> str:
        height, width = image.shape[:2]
        # Flowchart borders (especially diamonds) are commonly mistaken for
        # punctuation. Keep the central text area and discard OCR tokens that
        # still touch the processed crop boundary.
        inset_x = max(2.0, bbox.width * 0.15)
        inset_y = max(2.0, bbox.height * 0.18)
        x1 = max(0, int(bbox.x1 + inset_x))
        y1 = max(0, int(bbox.y1 + inset_y))
        x2 = min(width, int(bbox.x2 - inset_x))
        y2 = min(height, int(bbox.y2 - inset_y))
        if x2 <= x1 or y2 <= y1:
            return ""

        crop = image[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
        if gray.shape[0] < 128:
            scale = 128 / max(gray.shape[0], 1)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        processed = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]
        aspect_ratio = bbox.height / max(bbox.width, 1.0)
        page_segmentation_mode = 11 if aspect_ratio < 0.55 else 6

        try:
            data = self._pytesseract.image_to_data(
                processed,
                lang=self._language,
                config=f"--psm {page_segmentation_mode}",
                output_type=self._pytesseract.Output.DICT,
            )
        except self._pytesseract.TesseractError as exc:
            raise RuntimeError(
                f"O Tesseract falhou para o idioma '{self._language}'. "
                "Verifique se o pacote de idioma está instalado."
            ) from exc
        except self._pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(
                "Executável do Tesseract não encontrado. Instale-o ou informe "
                "--tesseract-cmd."
            ) from exc

        processed_height, processed_width = processed.shape[:2]
        tokens: list[str] = []
        for index, raw_text in enumerate(data["text"]):
            token = str(raw_text).strip()
            if not token or float(data["conf"][index]) < 25:
                continue

            left = int(data["left"][index])
            top = int(data["top"][index])
            token_width = int(data["width"][index])
            token_height = int(data["height"][index])
            touches_border = (
                left <= 1
                or top <= 1
                or left + token_width >= processed_width - 1
                or top + token_height >= processed_height - 1
            )
            if not touches_border:
                tokens.append(token)

        return " ".join(tokens)
