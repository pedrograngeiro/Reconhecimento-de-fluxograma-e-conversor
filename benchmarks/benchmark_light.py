"""Benchmark leve e reproduzível das etapas disponíveis sem YOLO/OCR.

Mede leitura da imagem, detecção de segmentos e a combinação das duas etapas.
Usa uma única thread do OpenCV e poucas repetições para máquinas limitadas.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import platform
from statistics import median
import time
from typing import Callable, TypeVar

import cv2

from flowchart_converter.preprocessing import load_pages
from flowchart_converter.topology import detect_line_segments


T = TypeVar("T")


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * 0.95 + 0.999) - 1))
    return ordered[index]


def measure(
    function: Callable[[], T], *, repeats: int, warmups: int = 2
) -> tuple[float, float, T]:
    result: T
    for _ in range(warmups):
        result = function()

    elapsed_ms: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = function()
        elapsed_ms.append((time.perf_counter() - start) * 1_000)
    return median(elapsed_ms), percentile_95(elapsed_ms), result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("benchmarks/online_samples/images"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/results/light_benchmark.csv"),
    )
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()
    if not 3 <= args.repeats <= 50:
        raise ValueError("Use entre 3 e 50 repetições.")

    cv2.setNumThreads(1)
    image_paths = sorted(args.images_dir.glob("*.png"))
    if not image_paths:
        raise FileNotFoundError(f"Nenhuma imagem PNG em {args.images_dir}")

    rows: list[dict[str, str | int | float]] = []
    for path in image_paths:
        decode_median, decode_p95, pages = measure(
            lambda: load_pages(path), repeats=args.repeats
        )
        image = pages[0].image
        line_median, line_p95, segments = measure(
            lambda: detect_line_segments(image, []), repeats=args.repeats
        )

        def light_pipeline() -> int:
            loaded = load_pages(path)[0].image
            return len(detect_line_segments(loaded, []))

        total_median, total_p95, _ = measure(
            light_pipeline, repeats=args.repeats
        )
        height, width = image.shape[:2]
        rows.append(
            {
                "file": path.name,
                "width_px": width,
                "height_px": height,
                "megapixels": round(width * height / 1_000_000, 4),
                "size_bytes": path.stat().st_size,
                "segments": len(segments),
                "decode_median_ms": round(decode_median, 3),
                "decode_p95_ms": round(decode_p95, 3),
                "lines_median_ms": round(line_median, 3),
                "lines_p95_ms": round(line_p95, 3),
                "light_total_median_ms": round(total_median, 3),
                "light_total_p95_ms": round(total_p95, 3),
                "repeats": args.repeats,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Ambiente: {platform.platform()}")
    print(f"OpenCV: {cv2.__version__}; threads: 1; repetições: {args.repeats}")
    for row in rows:
        print(
            f"{row['file']}: {row['width_px']}x{row['height_px']}, "
            f"total mediano {row['light_total_median_ms']} ms, "
            f"p95 {row['light_total_p95_ms']} ms"
        )
    print(f"Resultado: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
