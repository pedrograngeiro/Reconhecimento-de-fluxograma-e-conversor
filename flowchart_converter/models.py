"""Modelos de dados usados entre reconhecimento, topologia e renderização."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from math import hypot
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class BBox:
    """Caixa delimitadora no formato ``x1, y1, x2, y2`` em pixels."""

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError(f"Caixa inválida: {self}")

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def distance_to_point(self, point: tuple[float, float]) -> float:
        """Distância euclidiana de um ponto à borda (zero quando interno)."""

        x, y = point
        dx = max(self.x1 - x, 0, x - self.x2)
        dy = max(self.y1 - y, 0, y - self.y2)
        return hypot(dx, dy)

    def as_list(self) -> list[float]:
        return [round(self.x1, 3), round(self.y1, 3), round(self.x2, 3), round(self.y2, 3)]


@dataclass(frozen=True, slots=True)
class Detection:
    """Predição normalizada produzida por um detector."""

    label: str
    confidence: float
    bbox: BBox


@dataclass(slots=True)
class Node:
    id: str
    kind: str
    bbox: BBox
    confidence: float
    text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.kind,
            "text": self.text,
            "bbox": self.bbox.as_list(),
            "confidence": round(self.confidence, 5),
        }


@dataclass(frozen=True, slots=True)
class Edge:
    id: str
    source: str
    target: str
    confidence: float
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["confidence"] = round(self.confidence, 5)
        return data


@dataclass(slots=True)
class FlowchartGraph:
    nodes: list[Node]
    edges: list[Edge]
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("O grafo contém IDs de nós duplicados.")
        valid_ids = set(ids)
        for edge in self.edges:
            if edge.source not in valid_ids or edge.target not in valid_ids:
                raise ValueError(f"A aresta {edge.id} referencia um nó inexistente.")
            if edge.source == edge.target:
                raise ValueError(f"A aresta {edge.id} forma um laço não suportado pelo MVP.")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": "1.0",
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": self.metadata,
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
