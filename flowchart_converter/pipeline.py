"""Orquestração ponta a ponta do conversor."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .detection import Detector, YoloDetector, partition_detections
from .models import FlowchartGraph, Node
from .ocr import OcrEngine, TesseractOcr
from .preprocessing import load_pages
from .rendering import write_graph_outputs
from .topology import TopologyBuilder, detect_line_segments


@dataclass(frozen=True, slots=True)
class ConversionConfig:
    model_path: Path
    output_dir: Path = Path("output")
    confidence: float = 0.25
    use_ocr: bool = True
    ocr_language: str = "por"
    tesseract_cmd: str | None = None
    dpi: int = 200
    formats: tuple[str, ...] = ("svg",)
    rankdir: str = "TB"


@dataclass(slots=True)
class ConversionResult:
    graph: FlowchartGraph
    outputs: list[Path]
    warnings: list[str] = field(default_factory=list)


class FlowchartConverter:
    def __init__(
        self,
        config: ConversionConfig,
        *,
        detector: Detector | None = None,
        ocr_engine: OcrEngine | None = None,
        topology_builder: TopologyBuilder | None = None,
    ) -> None:
        self.config = config
        self.detector = detector or YoloDetector(config.model_path, config.confidence)
        self.topology_builder = topology_builder or TopologyBuilder()
        self._ocr_warning: str | None = None

        if not config.use_ocr:
            self.ocr_engine = None
        elif ocr_engine is not None:
            self.ocr_engine = ocr_engine
        else:
            try:
                self.ocr_engine = TesseractOcr(
                    language=config.ocr_language,
                    executable=config.tesseract_cmd,
                )
            except RuntimeError as exc:
                self.ocr_engine = None
                self._ocr_warning = str(exc)

    def convert(self, input_path: Path | str) -> list[ConversionResult]:
        input_path = Path(input_path)
        pages = load_pages(input_path, dpi=self.config.dpi)
        results: list[ConversionResult] = []
        is_multipage = len(pages) > 1 or input_path.suffix.lower() == ".pdf"
        for page in pages:
            stem = input_path.stem
            if is_multipage:
                stem = f"{stem}-page-{page.number:03d}"
            results.append(
                self.convert_page(
                    page.image,
                    source=str(input_path),
                    page_number=page.number,
                    output_stem=stem,
                )
            )
        return results

    def convert_page(
        self,
        image: np.ndarray,
        *,
        source: str,
        page_number: int,
        output_stem: str,
    ) -> ConversionResult:
        detections = self.detector.detect(image)
        node_detections, arrowheads = partition_detections(detections)
        node_detections.sort(key=lambda item: (item.bbox.center[1], item.bbox.center[0]))

        warnings = [self._ocr_warning] if self._ocr_warning else []
        nodes: list[Node] = []
        for index, detection in enumerate(node_detections, start=1):
            text = ""
            if self.ocr_engine is not None:
                try:
                    text = self.ocr_engine.read(image, detection.bbox)
                except RuntimeError as exc:
                    warning = str(exc)
                    if warning not in warnings:
                        warnings.append(warning)
                    self.ocr_engine = None
            nodes.append(
                Node(
                    id=f"n{index}",
                    kind=detection.label,
                    bbox=detection.bbox,
                    confidence=detection.confidence,
                    text=text,
                )
            )

        segments = detect_line_segments(image, [node.bbox for node in nodes])
        edges = self.topology_builder.build(nodes, arrowheads, segments, image.shape)
        graph = FlowchartGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "source": source,
                "page": page_number,
                "detections": len(detections),
                "arrowheads": len(arrowheads),
                "line_segments": len(segments),
            },
        )
        outputs, render_warnings = write_graph_outputs(
            graph,
            self.config.output_dir,
            output_stem,
            formats=self.config.formats,
            rankdir=self.config.rankdir,
        )
        warnings.extend(render_warnings)
        return ConversionResult(graph=graph, outputs=outputs, warnings=warnings)
