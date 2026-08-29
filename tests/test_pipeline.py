from pathlib import Path

import numpy as np

from flowchart_converter.models import BBox, Detection
from flowchart_converter.pipeline import ConversionConfig, FlowchartConverter


class FakeDetector:
    def detect(self, image: np.ndarray) -> list[Detection]:
        return [
            Detection("process", 0.9, BBox(10, 10, 90, 50)),
            Detection("decision", 0.8, BBox(10, 100, 90, 150)),
        ]


class FakeOcr:
    def read(self, image: np.ndarray, bbox: BBox) -> str:
        return "Texto"


class UnknownSymbolDetector:
    def detect(self, image: np.ndarray) -> list[Detection]:
        return [Detection("custom_shape", 0.75, BBox(10, 10, 90, 50))]


def test_page_conversion_writes_auditable_outputs(tmp_path) -> None:
    config = ConversionConfig(
        model_path=Path("unused.pt"),
        output_dir=tmp_path,
        formats=(),
    )
    converter = FlowchartConverter(config, detector=FakeDetector(), ocr_engine=FakeOcr())
    image = np.full((180, 120, 3), 255, dtype=np.uint8)

    result = converter.convert_page(
        image,
        source="demo.png",
        page_number=1,
        output_stem="demo",
    )

    assert len(result.graph.nodes) == 2
    assert all(node.text == "Texto" for node in result.graph.nodes)
    assert result.graph.schema_version == "1.1"
    assert result.graph.metadata["canvas"] == {"width_px": 120, "height_px": 180}
    assert (tmp_path / "demo.json").is_file()
    assert (tmp_path / "demo.dot").is_file()


def test_page_conversion_normalizes_unknown_detector_labels(tmp_path) -> None:
    config = ConversionConfig(
        model_path=Path("unused.pt"),
        output_dir=tmp_path,
        formats=(),
        use_ocr=False,
    )
    converter = FlowchartConverter(config, detector=UnknownSymbolDetector())

    result = converter.convert_page(
        np.full((80, 100, 3), 255, dtype=np.uint8),
        source="demo.png",
        page_number=1,
        output_stem="demo",
    )

    assert result.graph.nodes[0].kind == "unknown"
    assert result.graph.nodes[0].source_type == "custom_shape"
    assert "custom_shape" in result.warnings[0]
