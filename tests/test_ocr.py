from types import SimpleNamespace

import numpy as np

from flowchart_converter.models import BBox
from flowchart_converter.ocr import TesseractOcr


class FakePytesseract:
    Output = SimpleNamespace(DICT="dict")

    def __init__(self) -> None:
        self.processed_shape: tuple[int, ...] | None = None
        self.config: str | None = None

    def image_to_data(self, image, *, lang, config, output_type):
        self.processed_shape = image.shape
        self.config = config
        height, width = image.shape[:2]
        return {
            "text": ["border", "Dia", "de", "sol?", "edge"],
            "conf": [80, 93, 93, 64, 70],
            "left": [0, width // 4, width // 2, width // 3, width - 10],
            "top": [0, height // 3, height // 3, height // 2, height - 10],
            "width": [20, 24, 20, 30, 10],
            "height": [20, 20, 20, 20, 10],
        }


def test_ocr_upscales_crop_and_discards_shape_border_tokens() -> None:
    image = np.full((100, 200, 3), 210, dtype=np.uint8)
    engine = TesseractOcr(language="por")
    fake = FakePytesseract()
    engine._pytesseract = fake

    text = engine.read(image, BBox(50, 10, 150, 90))

    assert text == "Dia de sol?"
    assert fake.processed_shape is not None
    assert fake.processed_shape[0] >= 128
    assert fake.config == "--psm 6"
