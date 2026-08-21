"""Serialização DOT e renderização vetorial por Graphviz."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from .models import FlowchartGraph, Node


GRAPHVIZ_SHAPES = {
    "decision": "diamond",
    "decisao": "diamond",
    "terminator": "ellipse",
    "start_end": "ellipse",
    "inicio_fim": "ellipse",
    "input_output": "parallelogram",
    "entrada_saida": "parallelogram",
    "connector": "circle",
    "conector": "circle",
}


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _node_line(node: Node) -> str:
    normalized = node.kind.lower().strip().replace(" ", "_")
    shape = GRAPHVIZ_SHAPES.get(normalized, "box")
    label = node.text or node.kind.replace("_", " ").title()
    attributes = [
        f"label={_quote(label)}",
        f"shape={shape}",
        'fontname="Arial"',
        'fontsize="11"',
        'color="#334155"',
        'fillcolor="#f8fafc"',
        'fontcolor="#0f172a"',
        'style="rounded,filled"' if shape == "box" else 'style="filled"',
        'margin="0.16,0.10"',
    ]
    return f"  {_quote(node.id)} [{', '.join(attributes)}];"


def to_dot(graph: FlowchartGraph, rankdir: str = "TB") -> str:
    graph.validate()
    if rankdir not in {"TB", "BT", "LR", "RL"}:
        raise ValueError("rankdir deve ser TB, BT, LR ou RL.")

    lines = [
        "digraph flowchart {",
        f"  rankdir={rankdir};",
        '  graph [bgcolor="white", pad="0.25", nodesep="0.45", ranksep="0.60", splines=ortho];',
        '  edge [color="#64748b", penwidth="1.5", arrowsize="0.8", fontname="Arial", fontsize="10"];',
    ]
    lines.extend(_node_line(node) for node in graph.nodes)
    for edge in graph.edges:
        attributes = f" [label={_quote(edge.label)}]" if edge.label else ""
        lines.append(f"  {_quote(edge.source)} -> {_quote(edge.target)}{attributes};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_graph_outputs(
    graph: FlowchartGraph,
    output_dir: Path,
    stem: str,
    *,
    formats: tuple[str, ...] = ("svg",),
    rankdir: str = "TB",
) -> tuple[list[Path], list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    dot_path = output_dir / f"{stem}.dot"
    graph.write_json(json_path)
    dot_path.write_text(to_dot(graph, rankdir=rankdir), encoding="utf-8")
    outputs = [json_path, dot_path]
    warnings: list[str] = []

    unsupported = set(formats) - {"svg", "png", "pdf"}
    if unsupported:
        raise ValueError(f"Formatos não suportados: {', '.join(sorted(unsupported))}")
    if not formats:
        return outputs, warnings

    dot_executable = shutil.which("dot")
    if not dot_executable:
        warnings.append(
            "Graphviz não foi encontrado; JSON e DOT foram gerados, mas a imagem não."
        )
        return outputs, warnings

    for output_format in formats:
        rendered_path = output_dir / f"{stem}.{output_format}"
        completed = subprocess.run(
            [dot_executable, f"-T{output_format}", str(dot_path), "-o", str(rendered_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if completed.returncode != 0:
            warnings.append(
                f"Graphviz falhou ao gerar {output_format}: {completed.stderr.strip()}"
            )
        else:
            outputs.append(rendered_path)
    return outputs, warnings
