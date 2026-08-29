"""CLI para renderizar novamente um grafo JSON no padrão visual do projeto."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .models import FlowchartGraph
from .rendering import PublicationOptions, publish_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flowchart-render",
        description="Renderiza um JSON de fluxograma como SVG, PDF ou PNG padronizado.",
    )
    parser.add_argument("input", type=Path, help="Grafo JSON no schema 1.0 ou 1.1.")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--name", help="Nome-base dos arquivos gerados.")
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=("svg", "png", "pdf"),
        help="Formato renderizado; pode ser repetido. Padrão: svg.",
    )
    parser.add_argument("--rankdir", choices=("TB", "BT", "LR", "RL"), default="TB")
    parser.add_argument(
        "--page-size",
        choices=("content", "a4"),
        default="content",
        help="Ajusta ao conteúdo ou limita a publicação a uma página A4.",
    )
    parser.add_argument(
        "--orientation",
        choices=("portrait", "landscape"),
        default="portrait",
    )
    parser.add_argument("--dpi", type=int, default=300, help="Resolução do PNG.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        graph = FlowchartGraph.read_json(args.input)
        stem = args.name or args.input.stem
        target_json = (args.output_dir / f"{stem}.json").resolve()
        if target_json == args.input.resolve():
            raise ValueError(
                "A publicação não pode sobrescrever o JSON de origem; "
                "use --output-dir ou --name diferente."
            )
        result = publish_graph(
            graph,
            PublicationOptions(
                output_dir=args.output_dir,
                stem=stem,
                formats=tuple(args.formats or ("svg",)),
                rankdir=args.rankdir,
                page_size=args.page_size,
                orientation=args.orientation,
                dpi=args.dpi,
            ),
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    for output in result.artifacts:
        print(f"gerado: {output}")
    for warning in result.warnings:
        print(f"aviso: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
