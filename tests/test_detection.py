from flowchart_converter.detection import partition_detections
from flowchart_converter.models import BBox, Detection


def test_partition_recognizes_arrow_aliases() -> None:
    detections = [
        Detection("decision", 0.9, BBox(0, 0, 10, 10)),
        Detection("arrow_head", 0.8, BBox(20, 20, 25, 25)),
    ]

    nodes, arrows = partition_detections(detections)

    assert [item.label for item in nodes] == ["decision"]
    assert [item.label for item in arrows] == ["arrow_head"]
