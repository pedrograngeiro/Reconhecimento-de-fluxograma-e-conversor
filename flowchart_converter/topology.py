"""Detecção de conectores e reconstrução da topologia do fluxograma."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

import cv2
import numpy as np

from .models import BBox, Detection, Edge, Node


@dataclass(frozen=True, slots=True)
class LineSegment:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def points(self) -> tuple[tuple[float, float], tuple[float, float]]:
        return ((self.x1, self.y1), (self.x2, self.y2))

    @property
    def length(self) -> float:
        return hypot(self.x2 - self.x1, self.y2 - self.y1)


def detect_line_segments(
    image: np.ndarray,
    node_boxes: list[BBox],
    *,
    min_line_length: int = 24,
    max_line_gap: int = 16,
) -> list[LineSegment]:
    """Encontra segmentos fora das formas, onde normalmente estão as arestas."""

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 50, 150)

    height, width = edges.shape
    for bbox in node_boxes:
        x1 = max(0, int(bbox.x1) - 1)
        y1 = max(0, int(bbox.y1) - 1)
        x2 = min(width, int(bbox.x2) + 2)
        y2 = min(height, int(bbox.y2) + 2)
        edges[y1:y2, x1:x2] = 0

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=18,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap,
    )
    if lines is None:
        return []

    segments = [LineSegment(*(float(value) for value in line[0])) for line in lines]
    return sorted(segments, key=lambda segment: segment.length, reverse=True)


def _point_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def _distance_to_segment(point: tuple[float, float], segment: LineSegment) -> float:
    px, py = point
    vx, vy = segment.x2 - segment.x1, segment.y2 - segment.y1
    squared_length = vx * vx + vy * vy
    if squared_length == 0:
        return _point_distance(point, (segment.x1, segment.y1))
    projection = ((px - segment.x1) * vx + (py - segment.y1) * vy) / squared_length
    projection = min(1.0, max(0.0, projection))
    closest = (segment.x1 + projection * vx, segment.y1 + projection * vy)
    return _point_distance(point, closest)


def _segments_touch(a: LineSegment, b: LineSegment, tolerance: float) -> bool:
    return min(_point_distance(pa, pb) for pa in a.points for pb in b.points) <= tolerance


class TopologyBuilder:
    """Associa pontas de seta, linhas e nós com regras geométricas explícitas."""

    def __init__(self, join_tolerance: float = 18.0) -> None:
        self.join_tolerance = join_tolerance

    def build(
        self,
        nodes: list[Node],
        arrowheads: list[Detection],
        segments: list[LineSegment],
        image_shape: tuple[int, ...],
    ) -> list[Edge]:
        if len(nodes) < 2 or not arrowheads or not segments:
            return []

        height, width = image_shape[:2]
        snap_limit = max(30.0, hypot(width, height) * 0.05)
        edges: list[Edge] = []
        seen_pairs: set[tuple[str, str]] = set()

        ordered_arrows = sorted(arrowheads, key=lambda item: (item.bbox.center[1], item.bbox.center[0]))
        for arrow in ordered_arrows:
            arrow_center = arrow.bbox.center
            target = min(nodes, key=lambda node: node.bbox.distance_to_point(arrow_center))
            target_distance = target.bbox.distance_to_point(arrow_center)
            if target_distance > snap_limit:
                continue

            distances = [_distance_to_segment(arrow_center, segment) for segment in segments]
            seed_index = min(range(len(segments)), key=distances.__getitem__)
            if distances[seed_index] > snap_limit:
                continue

            component = self._connected_component(seed_index, segments)
            component_points = [point for index in component for point in segments[index].points]
            source_candidates = [node for node in nodes if node.id != target.id]
            source = min(
                source_candidates,
                key=lambda node: min(node.bbox.distance_to_point(point) for point in component_points),
            )
            source_distance = min(
                source.bbox.distance_to_point(point) for point in component_points
            )
            if source_distance > snap_limit:
                continue

            pair = (source.id, target.id)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            geometry_score = max(0.0, 1 - (target_distance + source_distance) / (2 * snap_limit))
            edges.append(
                Edge(
                    id=f"e{len(edges) + 1}",
                    source=source.id,
                    target=target.id,
                    confidence=arrow.confidence * geometry_score,
                )
            )
        return edges

    def _connected_component(
        self, seed_index: int, segments: list[LineSegment]
    ) -> set[int]:
        component = {seed_index}
        pending = [seed_index]
        while pending:
            current = pending.pop()
            for candidate in range(len(segments)):
                if candidate in component:
                    continue
                if _segments_touch(
                    segments[current], segments[candidate], self.join_tolerance
                ):
                    component.add(candidate)
                    pending.append(candidate)
        return component
