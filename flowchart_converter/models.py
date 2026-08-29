"""Modelos de dados usados entre reconhecimento, topologia e renderização."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from math import hypot
from pathlib import Path
from typing import Any


CURRENT_SCHEMA_VERSION = "1.1"
SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0", CURRENT_SCHEMA_VERSION})
SYMBOL_KINDS = frozenset(
    {"process", "decision", "terminator", "input_output", "connector", "unknown"}
)
SYMBOL_ALIASES = {
    "node": "process",
    "action": "process",
    "acao": "process",
    "decisao": "decision",
    "start_end": "terminator",
    "inicio_fim": "terminator",
    "entrada_saida": "input_output",
    "conector": "connector",
}
EDGE_BRANCHES = frozenset({"yes", "no", "default", "loop", "other"})


def _normalized_identifier(value: str) -> str:
    ascii_value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    return ascii_value.lower().strip().replace(" ", "_")


def canonical_symbol_kind(value: str) -> str:
    """Converte classes do detector e aliases legados para a taxonomia canônica."""

    normalized = _normalized_identifier(value)
    canonical = SYMBOL_ALIASES.get(normalized, normalized)
    return canonical if canonical in SYMBOL_KINDS else "unknown"


def _optional_confidence(data: dict[str, Any], field_name: str) -> float | None:
    value = data.get(field_name)
    return None if value is None else float(value)


def _optional_string(data: dict[str, Any], field_name: str) -> str | None:
    value = data.get(field_name)
    return None if value is None else str(value)


def _validate_confidence(value: float | None, field_name: str) -> None:
    if value is not None and not 0 <= value <= 1:
        raise ValueError(f"{field_name} deve estar entre 0 e 1.")


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
        return [
            round(self.x1, 3),
            round(self.y1, 3),
            round(self.x2, 3),
            round(self.y2, 3),
        ]


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
    bbox: BBox | None = None
    confidence: float | None = None
    text: str = ""
    source_type: str | None = None
    ocr_confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.kind,
            "text": self.text,
        }
        if self.bbox is not None:
            data["bbox"] = self.bbox.as_list()
        if self.confidence is not None:
            data["confidence"] = round(self.confidence, 5)
        if self.source_type is not None:
            data["source_type"] = self.source_type
        if self.ocr_confidence is not None:
            data["ocr_confidence"] = round(self.ocr_confidence, 5)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Node:
        try:
            raw_bbox = data.get("bbox")
            bbox = (
                None
                if raw_bbox is None
                else BBox(*(float(value) for value in raw_bbox))
            )
            return cls(
                id=str(data["id"]),
                kind=str(data["type"]),
                text=str(data.get("text", "")),
                bbox=bbox,
                confidence=_optional_confidence(data, "confidence"),
                source_type=_optional_string(data, "source_type"),
                ocr_confidence=_optional_confidence(data, "ocr_confidence"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Nó JSON inválido: {data!r}") from exc


@dataclass(frozen=True, slots=True)
class Edge:
    id: str
    source: str
    target: str
    confidence: float | None = None
    label: str = ""
    branch: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
        }
        if self.confidence is not None:
            data["confidence"] = round(self.confidence, 5)
        if self.branch is not None:
            data["branch"] = self.branch
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Edge:
        try:
            return cls(
                id=str(data["id"]),
                source=str(data["source"]),
                target=str(data["target"]),
                confidence=_optional_confidence(data, "confidence"),
                label=str(data.get("label") or ""),
                branch=_optional_string(data, "branch"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Aresta JSON inválida: {data!r}") from exc


@dataclass(slots=True)
class FlowchartGraph:
    nodes: list[Node]
    edges: list[Edge]
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = CURRENT_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(f"schema_version não suportada: {self.schema_version}.")
        ids = [node.id for node in self.nodes]
        if any(not node_id.strip() for node_id in ids):
            raise ValueError("Todo nó deve possuir um ID não vazio.")
        if len(ids) != len(set(ids)):
            raise ValueError("O grafo contém IDs de nós duplicados.")
        for node in self.nodes:
            if (
                self.schema_version == CURRENT_SCHEMA_VERSION
                and node.kind not in SYMBOL_KINDS
            ):
                raise ValueError(
                    f"Tipo de símbolo não canônico no nó {node.id}: {node.kind}."
                )
            _validate_confidence(node.confidence, f"confidence do nó {node.id}")
            _validate_confidence(
                node.ocr_confidence, f"ocr_confidence do nó {node.id}"
            )
        valid_ids = set(ids)
        for edge in self.edges:
            if edge.source not in valid_ids or edge.target not in valid_ids:
                raise ValueError(f"A aresta {edge.id} referencia um nó inexistente.")
            if edge.source == edge.target:
                raise ValueError(
                    f"A aresta {edge.id} forma um laço não suportado pelo MVP."
                )
            _validate_confidence(edge.confidence, f"confidence da aresta {edge.id}")
            if edge.branch is not None and edge.branch not in EDGE_BRANCHES:
                raise ValueError(f"Ramo inválido na aresta {edge.id}: {edge.branch}.")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FlowchartGraph:
        schema_version = str(data.get("schema_version", ""))
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            supported = ", ".join(sorted(SUPPORTED_SCHEMA_VERSIONS))
            raise ValueError(f"O JSON deve usar schema_version {supported}.")
        try:
            raw_nodes = data["nodes"]
            raw_edges = data["edges"]
            if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
                raise TypeError("nodes e edges devem ser listas")
            metadata = data.get("metadata", {})
            if not isinstance(metadata, dict):
                raise TypeError("metadata deve ser um objeto")
            graph = cls(
                nodes=[Node.from_dict(item) for item in raw_nodes],
                edges=[Edge.from_dict(item) for item in raw_edges],
                metadata=metadata,
                schema_version=schema_version,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Estrutura de grafo JSON inválida.") from exc
        graph.validate()
        return graph

    @classmethod
    def read_json(cls, path: Path) -> FlowchartGraph:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON inválido em {path}: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("A raiz do JSON deve ser um objeto.")
        return cls.from_dict(data)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
