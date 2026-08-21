from flowchart_converter.models import BBox, Edge, FlowchartGraph, Node
from flowchart_converter.rendering import to_dot, write_graph_outputs


def _graph() -> FlowchartGraph:
    return FlowchartGraph(
        nodes=[
            Node("n1", "process", BBox(0, 0, 80, 40), 0.9, 'Ler "arquivo"'),
            Node("n2", "decision", BBox(0, 80, 80, 120), 0.9, "Válido?"),
        ],
        edges=[Edge("e1", "n1", "n2", 0.8)],
    )


def test_dot_escapes_text_and_maps_decision_shape() -> None:
    dot = to_dot(_graph())

    assert 'Ler \\"arquivo\\"' in dot
    assert "shape=diamond" in dot
    assert '"n1" -> "n2"' in dot


def test_json_and_dot_do_not_require_graphviz(tmp_path) -> None:
    outputs, warnings = write_graph_outputs(_graph(), tmp_path, "demo", formats=())

    assert {path.suffix for path in outputs} == {".json", ".dot"}
    assert warnings == []


def test_missing_graphviz_keeps_structured_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("flowchart_converter.rendering.shutil.which", lambda _: None)

    outputs, warnings = write_graph_outputs(_graph(), tmp_path, "demo")

    assert {path.suffix for path in outputs} == {".json", ".dot"}
    assert warnings == [
        "Graphviz não foi encontrado; JSON e DOT foram gerados, mas a imagem não."
    ]
