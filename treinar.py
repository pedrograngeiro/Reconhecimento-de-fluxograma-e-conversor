"""Treina ou retoma o treinamento do detector YOLO do projeto."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("flow-chart/data.yaml"))
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("yolov8n.pt"),
        help="Pesos-base para treino novo ou checkpoint last.pt para retomada.",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--project", type=Path, default=Path("runs/flowchart"))
    parser.add_argument("--name", default="detector")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Retoma exatamente o checkpoint informado em --model.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.data.is_file():
        raise FileNotFoundError(f"Configuração do dataset não encontrada: {args.data}")
    if args.resume and args.model.name != "last.pt":
        print("aviso: --resume normalmente deve apontar para um arquivo last.pt")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Ultralytics não está instalado. Execute: pip install -e \".[ml]\""
        ) from exc

    model = YOLO(str(args.model))
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        device=args.device,
        project=str(args.project),
        name=args.name,
        seed=args.seed,
        deterministic=True,
        resume=args.resume,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
