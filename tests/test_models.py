import pytest

from flowchart_converter.models import BBox, Edge, FlowchartGraph, Node


def test_graph_serialization_uses_versioned_schema() -> None:
    graph = FlowchartGraph(
        nodes=[Node("n1", "process", BBox(1, 2, 30, 40), 0.912345, "Validar")],
        edges=[],
        metadata={"source": "demo.png"},
    )

    data = graph.to_dict()

    assert data["schema_version"] == "1.0"
    assert data["nodes"][0]["text"] == "Validar"
    assert data["nodes"][0]["confidence"] == 0.91234


def test_graph_rejects_edge_to_unknown_node() -> None:
    graph = FlowchartGraph(
        nodes=[Node("n1", "process", BBox(0, 0, 10, 10), 1.0)],
        edges=[Edge("e1", "n1", "n2", 0.8)],
    )

    with pytest.raises(ValueError, match="inexistente"):
        graph.validate()
