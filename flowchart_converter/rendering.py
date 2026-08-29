"""Serialização DOT e renderização no padrão visual do projeto."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import textwrap

import cv2
import numpy as np

from .models import FlowchartGraph, Node, canonical_symbol_kind


SUPPORTED_FORMATS = frozenset({"svg", "png", "pdf"})
RANK_DIRECTIONS = frozenset({"TB", "BT", "LR", "RL"})
PAGE_SIZES = frozenset({"content", "a4"})
ORIENTATIONS = frozenset({"portrait", "landscape"})


@dataclass(frozen=True, slots=True)
class NodeStyle:
    shape: str
    fill: str
    border: str
    style: str = "filled"
    margin: str = "0.18,0.12"
    width: float | None = None
    height: float | None = None
    fixed_size: bool = False


@dataclass(frozen=True, slots=True)
class PublicationOptions:
    output_dir: Path
    stem: str
    formats: tuple[str, ...] = ("svg",)
    rankdir: str = "TB"
    page_size: str = "content"
    orientation: str = "portrait"
    dpi: int = 300
    visual_standard: str = "1.0"

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_dir", Path(self.output_dir))
        if (
            not self.stem
            or Path(self.stem).name != self.stem
            or self.stem in {".", ".."}
        ):
            raise ValueError("O nome-base da publicação deve ser um nome de arquivo simples.")
        unsupported = set(self.formats) - SUPPORTED_FORMATS
        if unsupported:
            raise ValueError(
                f"Formatos não suportados: {', '.join(sorted(unsupported))}"
            )
        if self.rankdir not in RANK_DIRECTIONS:
            raise ValueError("rankdir deve ser TB, BT, LR ou RL.")
        if self.page_size not in PAGE_SIZES:
            raise ValueError("page_size deve ser content ou a4.")
        if self.orientation not in ORIENTATIONS:
            raise ValueError("orientation deve ser portrait ou landscape.")
        if not 72 <= self.dpi <= 1200:
            raise ValueError("dpi deve estar entre 72 e 1200.")
        if self.visual_standard != "1.0":
            raise ValueError("Apenas o padrão visual 1.0 é suportado.")


@dataclass(frozen=True, slots=True)
class PublicationResult:
    artifacts: tuple[Path, ...]
    warnings: tuple[str, ...] = ()


STANDARD_NODE_STYLES = {
    "process": NodeStyle(
        shape="box",
        fill="#DBEAFE",
        border="#1D4ED8",
        style="rounded,filled",
    ),
    "decision": NodeStyle(shape="diamond", fill="#FEF3C7", border="#B45309"),
    "terminator": NodeStyle(shape="ellipse", fill="#DCFCE7", border="#15803D"),
    "input_output": NodeStyle(
        shape="parallelogram", fill="#EDE9FE", border="#6D28D9"
    ),
    "connector": NodeStyle(
        shape="circle",
        fill="#E2E8F0",
        border="#475569",
        margin="0.02,0.02",
        width=0.48,
        height=0.48,
        fixed_size=True,
    ),
}

UNKNOWN_NODE_STYLE = NodeStyle(
    shape="box",
    fill="#F1F5F9",
    border="#64748B",
    style="rounded,filled",
)

DEFAULT_LABELS = {
    "process": "Processo",
    "decision": "Decisão",
    "terminator": "Início / fim",
    "input_output": "Entrada / saída",
}


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _wrap_label(value: str, width: int) -> str:
    lines: list[str] = []
    for source_line in value.splitlines() or [""]:
        lines.extend(
            textwrap.wrap(
                source_line,
                width=width,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [""]
        )
    return "\n".join(lines)


def _node_line(node: Node) -> str:
    kind = canonical_symbol_kind(node.kind)
    style = STANDARD_NODE_STYLES.get(kind, UNKNOWN_NODE_STYLE)
    if node.text:
        label = node.text
    elif kind == "connector":
        label = node.id.upper()
    else:
        label = DEFAULT_LABELS.get(kind, node.kind.replace("_", " ").title())
    label = _wrap_label(label, width=20 if kind == "decision" else 28)
    attributes = [
        f"label={_quote(label)}",
        f"shape={style.shape}",
        'fontname="Arial"',
        'fontsize="11"',
        f'color="{style.border}"',
        f'fillcolor="{style.fill}"',
        'fontcolor="#0F172A"',
        'penwidth="1.8"',
        f'style="{style.style}"',
        f'margin="{style.margin}"',
    ]
    if style.width is not None:
        attributes.append(f'width="{style.width}"')
    if style.height is not None:
        attributes.append(f'height="{style.height}"')
    if style.fixed_size:
        attributes.append('fixedsize="true"')
    return f"  {_quote(node.id)} [{', '.join(attributes)}];"


def to_dot(
    graph: FlowchartGraph,
    rankdir: str = "TB",
    *,
    page_size: str = "content",
    orientation: str = "portrait",
) -> str:
    graph.validate()
    if rankdir not in RANK_DIRECTIONS:
        raise ValueError("rankdir deve ser TB, BT, LR ou RL.")
    if page_size not in PAGE_SIZES:
        raise ValueError("page_size deve ser content ou a4.")
    if orientation not in ORIENTATIONS:
        raise ValueError("orientation deve ser portrait ou landscape.")

    lines = [
        "digraph flowchart {",
        f"  rankdir={rankdir};",
        f"  graph [{', '.join(_graph_attributes(page_size, orientation))}];",
        '  edge [color="#475569", fontcolor="#334155", penwidth="1.6", arrowsize="0.75", arrowhead=normal, fontname="Arial", fontsize="10"];',
    ]
    lines.extend(_node_line(node) for node in graph.nodes)
    for edge in graph.edges:
        attributes = f" [label={_quote(edge.label)}]" if edge.label else ""
        lines.append(f"  {_quote(edge.source)} -> {_quote(edge.target)}{attributes};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _graph_attributes(page_size: str, orientation: str) -> list[str]:
    attributes = [
        'bgcolor="white"',
        'pad="0.35"',
        'nodesep="0.55"',
        'ranksep="0.75"',
        "splines=ortho",
        "outputorder=edgesfirst",
    ]
    if page_size == "a4":
        dimensions = "8.27,11.69!" if orientation == "portrait" else "11.69,8.27!"
        attributes.extend([f'size="{dimensions}"', 'margin="0.47"'])
    return attributes


def _find_dot_executable() -> str | None:
    executable = shutil.which("dot")
    if executable:
        return executable

    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles")
        if program_files:
            candidate = Path(program_files) / "Graphviz" / "bin" / "dot.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def _flatten_png_background(path: Path) -> None:
    """Converte transparência do Graphviz em fundo branco para publicação."""

    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise OSError(f"PNG gerado não pôde ser lido: {path}")
    if image.ndim != 3 or image.shape[2] != 4:
        return

    alpha = image[:, :, 3:4].astype(np.float32) / 255.0
    foreground = image[:, :, :3].astype(np.float32)
    opaque = foreground * alpha + 255.0 * (1.0 - alpha)
    if not cv2.imwrite(str(path), opaque.astype(np.uint8)):
        raise OSError(f"PNG gerado não pôde receber fundo branco: {path}")


def _render_format(
    dot_executable: str,
    dot_path: Path,
    rendered_path: Path,
    output_format: str,
    dpi: int,
) -> str | None:
    command = [dot_executable, f"-T{output_format}"]
    if output_format == "png":
        command.append(f"-Gdpi={dpi}")
    command.extend([str(dot_path), "-o", str(rendered_path)])
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        return f"Graphviz falhou ao gerar {output_format}: {completed.stderr.strip()}"
    if output_format == "png" and rendered_path.is_file():
        _flatten_png_background(rendered_path)
    return None


def publish_graph(
    graph: FlowchartGraph, options: PublicationOptions
) -> PublicationResult:
    """Publica um grafo validado sem expor detalhes do Graphviz aos chamadores."""

    options.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = options.output_dir / f"{options.stem}.json"
    dot_path = options.output_dir / f"{options.stem}.dot"
    graph.write_json(json_path)
    dot_path.write_text(
        to_dot(
            graph,
            rankdir=options.rankdir,
            page_size=options.page_size,
            orientation=options.orientation,
        ),
        encoding="utf-8",
    )
    artifacts = [json_path, dot_path]
    warnings: list[str] = []

    if not options.formats:
        return PublicationResult(tuple(artifacts))

    dot_executable = _find_dot_executable()
    if not dot_executable:
        warnings.append(
            "Graphviz não foi encontrado; JSON e DOT foram gerados, mas a imagem não."
        )
        return PublicationResult(tuple(artifacts), tuple(warnings))

    for output_format in options.formats:
        rendered_path = options.output_dir / f"{options.stem}.{output_format}"
        warning = _render_format(
            dot_executable,
            dot_path,
            rendered_path,
            output_format,
            options.dpi,
        )
        if warning:
            warnings.append(warning)
        else:
            artifacts.append(rendered_path)
    return PublicationResult(tuple(artifacts), tuple(warnings))
