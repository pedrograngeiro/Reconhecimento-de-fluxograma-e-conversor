from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from flowchart_converter.models import BBox, Edge, FlowchartGraph, Node
from flowchart_converter.rendering import PublicationOptions, publish_graph, to_dot


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
    assert 'fillcolor="#FEF3C7"' in dot
    assert 'color="#B45309"' in dot
    assert '"n1" -> "n2"' in dot


def test_standard_visual_language_maps_every_semantic_kind() -> None:
    graph = FlowchartGraph(
        nodes=[
            Node("start", "terminator", BBox(0, 0, 80, 40), 1, "Início"),
            Node("action", "process", BBox(0, 50, 80, 90), 1, "Validar pedido"),
            Node("choice", "decision", BBox(0, 100, 80, 140), 1, "Aprovado?"),
            Node("input", "input_output", BBox(0, 150, 80, 190), 1, "Ler dados"),
            Node("link", "connector", BBox(0, 200, 20, 220), 1),
        ],
        edges=[],
    )

    dot = to_dot(graph)

    assert 'shape=ellipse' in dot and 'fillcolor="#DCFCE7"' in dot
    assert 'shape=box' in dot and 'fillcolor="#DBEAFE"' in dot
    assert 'shape=diamond' in dot and 'fillcolor="#FEF3C7"' in dot
    assert 'shape=parallelogram' in dot and 'fillcolor="#EDE9FE"' in dot
    assert 'shape=circle' in dot and 'fillcolor="#E2E8F0"' in dot
    assert 'label="LINK"' in dot


def test_long_labels_are_wrapped_for_consistent_node_width() -> None:
    graph = FlowchartGraph(
        nodes=[
            Node(
                "n1",
                "process",
                BBox(0, 0, 80, 40),
                1,
                "Cadastrar colaborador no sistema corporativo principal",
            )
        ],
        edges=[],
    )

    dot = to_dot(graph)

    assert "Cadastrar colaborador no\\nsistema corporativo\\nprincipal" in dot


def test_json_and_dot_do_not_require_graphviz(tmp_path) -> None:
    result = publish_graph(
        _graph(), PublicationOptions(tmp_path, "demo", formats=())
    )

    assert {path.suffix for path in result.artifacts} == {".json", ".dot"}
    assert result.warnings == ()


def test_missing_graphviz_keeps_structured_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("flowchart_converter.rendering._find_dot_executable", lambda: None)

    result = publish_graph(_graph(), PublicationOptions(tmp_path, "demo"))

    assert {path.suffix for path in result.artifacts} == {".json", ".dot"}
    assert result.warnings == (
        "Graphviz não foi encontrado; JSON e DOT foram gerados, mas a imagem não."
    ,)


def test_a4_profile_and_landscape_are_encoded_in_dot() -> None:
    dot = to_dot(_graph(), page_size="a4", orientation="landscape")

    assert 'size="11.69,8.27!"' in dot
    assert 'margin="0.47"' in dot


def test_png_publication_passes_requested_dpi_to_graphviz(tmp_path, monkeypatch) -> None:
    commands: list[list[str]] = []
    monkeypatch.setattr(
        "flowchart_converter.rendering._find_dot_executable", lambda: "dot"
    )

    def fake_run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("flowchart_converter.rendering.subprocess.run", fake_run)

    result = publish_graph(
        _graph(), PublicationOptions(tmp_path, "demo", formats=("png",), dpi=240)
    )

    assert "-Gdpi=240" in commands[0]
    assert result.artifacts[-1].suffix == ".png"


def test_png_publication_flattens_transparency_on_white(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "flowchart_converter.rendering._find_dot_executable", lambda: "dot"
    )

    def fake_run(command, **kwargs):
        output = command[command.index("-o") + 1]
        transparent = np.zeros((2, 2, 4), dtype=np.uint8)
        transparent[1, 1] = [0, 0, 255, 255]
        assert cv2.imwrite(output, transparent)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("flowchart_converter.rendering.subprocess.run", fake_run)

    result = publish_graph(
        _graph(), PublicationOptions(tmp_path, "demo", formats=("png",))
    )

    image = cv2.imread(str(result.artifacts[-1]), cv2.IMREAD_UNCHANGED)
    assert image.shape == (2, 2, 3)
    assert image[0, 0].tolist() == [255, 255, 255]
    assert image[1, 1].tolist() == [0, 0, 255]


def test_publication_rejects_path_in_output_stem(tmp_path) -> None:
    with pytest.raises(ValueError, match="nome-base"):
        PublicationOptions(tmp_path, "../fora")
