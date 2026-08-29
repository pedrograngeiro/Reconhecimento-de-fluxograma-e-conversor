import json

from flowchart_converter.models import FlowchartGraph
from flowchart_converter.render_cli import main


def _payload() -> dict:
    return {
        "schema_version": "1.0",
        "nodes": [
            {
                "id": "n1",
                "type": "terminator",
                "text": "Início",
                "bbox": [0, 0, 100, 40],
                "confidence": 1,
            },
            {
                "id": "n2",
                "type": "process",
                "text": "Executar ação",
                "bbox": [0, 60, 100, 100],
                "confidence": 1,
            },
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "confidence": 1,
                "label": "",
            }
        ],
        "metadata": {"source": "teste"},
    }


def test_graph_round_trips_from_json(tmp_path) -> None:
    source = tmp_path / "graph.json"
    source.write_text(json.dumps(_payload(), ensure_ascii=False), encoding="utf-8")

    graph = FlowchartGraph.read_json(source)

    assert graph.to_dict() == _payload()


def test_render_cli_creates_standard_dot_without_graphviz(tmp_path, monkeypatch) -> None:
    source = tmp_path / "graph.json"
    source.write_text(json.dumps(_payload(), ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "rendered"
    monkeypatch.setattr("flowchart_converter.rendering._find_dot_executable", lambda: None)

    exit_code = main(
        [
            str(source),
            "--output-dir",
            str(output),
            "--name",
            "standardized",
            "--format",
            "svg",
            "--page-size",
            "a4",
            "--orientation",
            "landscape",
        ]
    )

    assert exit_code == 0
    assert (output / "standardized.dot").is_file()
    assert not (output / "standardized.svg").exists()
    dot = (output / "standardized.dot").read_text(encoding="utf-8")
    assert 'fillcolor="#DCFCE7"' in dot
    assert 'fillcolor="#DBEAFE"' in dot
    assert 'size="11.69,8.27!"' in dot


def test_render_cli_does_not_overwrite_source_json(tmp_path) -> None:
    source = tmp_path / "graph.json"
    original = json.dumps(_payload(), ensure_ascii=False)
    source.write_text(original, encoding="utf-8")

    exit_code = main([str(source), "--output-dir", str(tmp_path), "--name", "graph"])

    assert exit_code == 2
    assert source.read_text(encoding="utf-8") == original
