import pytest

from flowchart_converter.models import (
    BBox,
    Edge,
    FlowchartGraph,
    Node,
    canonical_symbol_kind,
)


def test_graph_serialization_uses_versioned_schema() -> None:
    graph = FlowchartGraph(
        nodes=[Node("n1", "process", BBox(1, 2, 30, 40), 0.912345, "Validar")],
        edges=[],
        metadata={"source": "demo.png"},
    )

    data = graph.to_dict()

    assert data["schema_version"] == "1.1"
    assert data["nodes"][0]["text"] == "Validar"
    assert data["nodes"][0]["confidence"] == 0.91234


def test_schema_11_accepts_minimal_publishable_graph() -> None:
    graph = FlowchartGraph.from_dict(
        {
            "schema_version": "1.1",
            "nodes": [{"id": "n1", "type": "process", "text": "Validar"}],
            "edges": [],
        }
    )

    assert graph.nodes[0].bbox is None
    assert graph.nodes[0].confidence is None
    assert graph.to_dict()["nodes"][0] == {
        "id": "n1",
        "type": "process",
        "text": "Validar",
    }


def test_schema_11_rejects_noncanonical_symbol_kind() -> None:
    with pytest.raises(ValueError, match="Tipo de símbolo"):
        FlowchartGraph.from_dict(
            {
                "schema_version": "1.1",
                "nodes": [{"id": "n1", "type": "acao"}],
                "edges": [],
            }
        )


@pytest.mark.parametrize(
    ("source", "expected"),
    [("acao", "process"), ("Decisão", "decision"), ("qualquer_coisa", "unknown")],
)
def test_symbol_kind_normalization(source: str, expected: str) -> None:
    assert canonical_symbol_kind(source) == expected


def test_graph_rejects_edge_to_unknown_node() -> None:
    graph = FlowchartGraph(
        nodes=[Node("n1", "process", BBox(0, 0, 10, 10), 1.0)],
        edges=[Edge("e1", "n1", "n2", 0.8)],
    )

    with pytest.raises(ValueError, match="inexistente"):
        graph.validate()
