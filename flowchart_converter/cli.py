"""Interface de linha de comando do conversor."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .pipeline import ConversionConfig, FlowchartConverter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flowchart-converter",
        description="Reconhece um fluxograma e o reconstrói como grafo e diagrama vetorial.",
    )
    parser.add_argument("input", type=Path, help="Imagem ou PDF de entrada.")
    parser.add_argument("--model", type=Path, required=True, help="Pesos YOLO (.pt).")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--dpi", type=int, default=200, help="Resolução de PDFs.")
    parser.add_argument("--no-ocr", action="store_true", help="Desativa a leitura de texto.")
    parser.add_argument("--ocr-lang", default="por", help="Idioma instalado no Tesseract.")
    parser.add_argument("--tesseract-cmd", help="Caminho explícito do executável Tesseract.")
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=("svg", "png", "pdf"),
        help="Formato renderizado; pode ser repetido. Padrão: svg.",
    )
    parser.add_argument("--rankdir", choices=("TB", "BT", "LR", "RL"), default="TB")
    parser.add_argument("--page-size", choices=("content", "a4"), default="content")
    parser.add_argument(
        "--orientation",
        choices=("portrait", "landscape"),
        default="portrait",
    )
    parser.add_argument(
        "--output-dpi", type=int, default=300, help="Resolução da saída PNG."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = ConversionConfig(
        model_path=args.model,
        output_dir=args.output_dir,
        confidence=args.confidence,
        use_ocr=not args.no_ocr,
        ocr_language=args.ocr_lang,
        tesseract_cmd=args.tesseract_cmd,
        dpi=args.dpi,
        formats=tuple(args.formats or ("svg",)),
        rankdir=args.rankdir,
        page_size=args.page_size,
        orientation=args.orientation,
        render_dpi=args.output_dpi,
    )
    try:
        results = FlowchartConverter(config).convert(args.input)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    total_nodes = sum(len(result.graph.nodes) for result in results)
    total_edges = sum(len(result.graph.edges) for result in results)
    print(
        f"Conversão concluída: {len(results)} página(s), "
        f"{total_nodes} nó(s), {total_edges} conexão(ões)."
    )
    for result in results:
        for output in result.outputs:
            print(f"  gerado: {output}")
        for warning in result.warnings:
            print(f"  aviso: {warning}")
    return 0
