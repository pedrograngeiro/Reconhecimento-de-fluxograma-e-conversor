import cv2
import numpy as np

from flowchart_converter.models import BBox, Detection, Node
from flowchart_converter.topology import (
    LineSegment,
    TopologyBuilder,
    detect_line_segments,
)


def test_builder_connects_source_to_arrow_target() -> None:
    nodes = [
        Node("n1", "process", BBox(20, 20, 100, 80), 0.95),
        Node("n2", "decision", BBox(20, 180, 100, 240), 0.90),
    ]
    arrowheads = [Detection("arrow_head", 0.8, BBox(55, 168, 65, 178))]
    segments = [LineSegment(60, 82, 60, 169)]

    edges = TopologyBuilder().build(nodes, arrowheads, segments, (280, 140, 3))

    assert len(edges) == 1
    assert (edges[0].source, edges[0].target) == ("n1", "n2")
    assert 0 < edges[0].confidence <= 0.8


def test_builder_does_not_invent_edge_without_visible_line() -> None:
    nodes = [
        Node("n1", "process", BBox(0, 0, 20, 20), 1.0),
        Node("n2", "process", BBox(0, 80, 20, 100), 1.0),
    ]
    arrowheads = [Detection("arrow_head", 1.0, BBox(5, 70, 15, 78))]

    assert TopologyBuilder().build(nodes, arrowheads, [], (120, 40, 3)) == []


def test_opencv_detects_connector_between_masked_nodes() -> None:
    image = np.full((220, 160, 3), 255, dtype=np.uint8)
    boxes = [BBox(30, 20, 130, 70), BBox(30, 150, 130, 200)]
    for bbox in boxes:
        cv2.rectangle(
            image,
            (int(bbox.x1), int(bbox.y1)),
            (int(bbox.x2), int(bbox.y2)),
            (0, 0, 0),
            2,
        )
    cv2.line(image, (80, 72), (80, 148), (0, 0, 0), 2)

    segments = detect_line_segments(image, boxes)

    assert segments
    assert any(segment.length >= 60 for segment in segments)
