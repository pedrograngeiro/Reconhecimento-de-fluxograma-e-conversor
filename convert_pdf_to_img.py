"""Extrai páginas de um PDF como PNGs para inspeção ou anotação."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from flowchart_converter.preprocessing import load_pages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("pages"))
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    pages = load_pages(args.pdf, dpi=args.dpi)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for page in pages:
        destination = args.output_dir / f"{args.pdf.stem}-page-{page.number:03d}.png"
        if not cv2.imwrite(str(destination), page.image):
            raise RuntimeError(f"Não foi possível salvar: {destination}")
        print(f"gerado: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
