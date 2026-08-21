"""Adaptação do Ultralytics YOLO para o formato interno do projeto."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from .models import BBox, Detection


ARROW_ALIASES = {
    "arrow",
    "arrow_head",
    "arrowhead",
    "arrow-head",
    "ponta_de_seta",
    "seta",
}


class Detector(Protocol):
    def detect(self, image: np.ndarray) -> list[Detection]: ...


def is_arrow_label(label: str) -> bool:
    normalized = label.strip().lower().replace(" ", "_")
    return normalized in ARROW_ALIASES or "arrow" in normalized


def partition_detections(
    detections: list[Detection],
) -> tuple[list[Detection], list[Detection]]:
    """Separa pontas de seta; todas as demais classes são formas de nós."""

    nodes: list[Detection] = []
    arrows: list[Detection] = []
    for detection in detections:
        (arrows if is_arrow_label(detection.label) else nodes).append(detection)
    return nodes, arrows


class YoloDetector:
    """Detector carregado sob demanda para manter o núcleo testável sem YOLO."""

    def __init__(self, model_path: Path | str, confidence: float = 0.25) -> None:
        model_path = Path(model_path)
        if not model_path.is_file():
            raise FileNotFoundError(f"Modelo YOLO não encontrado: {model_path}")
        if not 0 < confidence <= 1:
            raise ValueError("A confiança deve estar entre 0 e 1.")

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics não está instalado. Execute: pip install -e \".[ml]\""
            ) from exc

        self._model = YOLO(str(model_path))
        self._confidence = confidence

    def detect(self, image: np.ndarray) -> list[Detection]:
        results = self._model.predict(
            source=image,
            conf=self._confidence,
            verbose=False,
        )
        if not results:
            return []

        result = results[0]
        names = result.names
        detections: list[Detection] = []
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            label = str(names.get(class_id, class_id))
            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
            detections.append(
                Detection(
                    label=label,
                    confidence=float(box.conf[0].item()),
                    bbox=BBox(x1, y1, x2, y2),
                )
            )
        return detections
