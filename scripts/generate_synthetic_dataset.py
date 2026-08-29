"""Gera um pequeno dataset YOLO sintético de elementos de fluxogramas."""

from __future__ import annotations

import argparse
import random
from collections import Counter
from pathlib import Path

import cv2
import numpy as np


IMAGE_SIZE = 640
CLASS_NAMES = (
    "process",
    "decision",
    "terminator",
    "input_output",
    "connector",
    "arrow_head",
)
NODE_LABELS = ("Inicio", "Ler dados", "Validar", "Processar", "Salvar", "Fim")
FILLS = (
    (239, 244, 255),
    (238, 252, 238),
    (250, 240, 252),
    (255, 247, 226),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("flow-chart"))
    parser.add_argument("--train", type=int, default=72)
    parser.add_argument("--val", type=int, default=18)
    parser.add_argument("--test", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def _box_to_yolo(class_id: int, box: tuple[int, int, int, int]) -> str:
    x1, y1, x2, y2 = box
    x_center = ((x1 + x2) / 2) / IMAGE_SIZE
    y_center = ((y1 + y2) / 2) / IMAGE_SIZE
    width = (x2 - x1) / IMAGE_SIZE
    height = (y2 - y1) / IMAGE_SIZE
    return f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"


def _draw_centered_text(
    image: np.ndarray, text: str, center: tuple[int, int], scale: float
) -> None:
    size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    origin = (center[0] - size[0] // 2, center[1] + size[1] // 2)
    cv2.putText(
        image,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (45, 45, 45),
        1,
        cv2.LINE_AA,
    )


def _draw_node(
    image: np.ndarray,
    class_id: int,
    center: tuple[int, int],
    rng: random.Random,
) -> tuple[int, int, int, int]:
    cx, cy = center
    outline = (rng.randint(15, 55),) * 3
    fill = rng.choice(FILLS)
    thickness = rng.choice((2, 3, 4))

    if class_id == 0:
        width, height = rng.randint(130, 175), rng.randint(55, 78)
        box = (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2)
        cv2.rectangle(image, box[:2], box[2:], fill, -1)
        cv2.rectangle(image, box[:2], box[2:], outline, thickness)
    elif class_id == 1:
        width, height = rng.randint(120, 155), rng.randint(82, 110)
        points = np.array(
            [(cx, cy - height // 2), (cx + width // 2, cy),
             (cx, cy + height // 2), (cx - width // 2, cy)],
            dtype=np.int32,
        )
        cv2.fillPoly(image, [points], fill)
        cv2.polylines(image, [points], True, outline, thickness, cv2.LINE_AA)
        box = (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2)
    elif class_id == 2:
        width, height = rng.randint(135, 175), rng.randint(50, 70)
        box = (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2)
        cv2.ellipse(image, (cx, cy), (width // 2, height // 2), 0, 0, 360, fill, -1)
        cv2.ellipse(
            image, (cx, cy), (width // 2, height // 2), 0, 0, 360,
            outline, thickness, cv2.LINE_AA,
        )
    elif class_id == 3:
        width, height = rng.randint(145, 180), rng.randint(55, 78)
        slant = rng.randint(18, 28)
        points = np.array(
            [(cx - width // 2 + slant, cy - height // 2),
             (cx + width // 2, cy - height // 2),
             (cx + width // 2 - slant, cy + height // 2),
             (cx - width // 2, cy + height // 2)],
            dtype=np.int32,
        )
        cv2.fillPoly(image, [points], fill)
        cv2.polylines(image, [points], True, outline, thickness, cv2.LINE_AA)
        box = (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2)
    else:
        radius = rng.randint(25, 38)
        box = (cx - radius, cy - radius, cx + radius, cy + radius)
        cv2.circle(image, (cx, cy), radius, fill, -1)
        cv2.circle(image, (cx, cy), radius, outline, thickness, cv2.LINE_AA)

    if class_id != 4:
        _draw_centered_text(image, rng.choice(NODE_LABELS), center, rng.uniform(0.42, 0.55))
    return box


def _edge_point(box: tuple[int, int, int, int], vertical: bool, outgoing: bool) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    if vertical:
        return ((x1 + x2) // 2, y2 if outgoing else y1)
    return (x2 if outgoing else x1, (y1 + y2) // 2)


def _draw_arrow(
    image: np.ndarray,
    start: tuple[int, int],
    end: tuple[int, int],
    vertical: bool,
    rng: random.Random,
) -> tuple[int, int, int, int]:
    color = (rng.randint(20, 65),) * 3
    thickness = rng.choice((2, 3, 4))
    tip = end
    length = rng.randint(12, 18)
    half_width = rng.randint(7, 11)
    if vertical:
        base_y = tip[1] - length
        line_end = (tip[0], base_y)
        triangle = np.array(
            [tip, (tip[0] - half_width, base_y), (tip[0] + half_width, base_y)],
            dtype=np.int32,
        )
        box = (tip[0] - half_width, base_y, tip[0] + half_width, tip[1])
    else:
        base_x = tip[0] - length
        line_end = (base_x, tip[1])
        triangle = np.array(
            [tip, (base_x, tip[1] - half_width), (base_x, tip[1] + half_width)],
            dtype=np.int32,
        )
        box = (base_x, tip[1] - half_width, tip[0], tip[1] + half_width)
    cv2.line(image, start, line_end, color, thickness, cv2.LINE_AA)
    cv2.fillPoly(image, [triangle], color)
    return box


def _generate_image(rng: random.Random, image_index: int) -> tuple[np.ndarray, list[str], Counter[int]]:
    background = rng.randint(244, 255)
    image = np.full((IMAGE_SIZE, IMAGE_SIZE, 3), background, dtype=np.uint8)
    vertical = image_index % 2 == 0
    node_count = rng.randint(3, 5)
    # A maior forma horizontal pode ter 180 px; 110 px evita recorte nas bordas.
    margin = 110
    primary = np.linspace(margin, IMAGE_SIZE - margin, node_count, dtype=int)
    secondary = IMAGE_SIZE // 2
    centers: list[tuple[int, int]] = []
    for position in primary:
        offset = rng.randint(-28, 28)
        centers.append((secondary + offset, int(position)) if vertical else (int(position), secondary + offset))

    class_ids = [(image_index + offset) % 5 for offset in range(node_count)]
    rng.shuffle(class_ids)
    boxes: list[tuple[int, int, int, int]] = []
    labels: list[str] = []
    counts: Counter[int] = Counter()
    for class_id, center in zip(class_ids, centers, strict=True):
        box = _draw_node(image, class_id, center, rng)
        boxes.append(box)
        labels.append(_box_to_yolo(class_id, box))
        counts[class_id] += 1

    for current, following in zip(boxes, boxes[1:], strict=False):
        start = _edge_point(current, vertical, outgoing=True)
        end = _edge_point(following, vertical, outgoing=False)
        arrow_box = _draw_arrow(image, start, end, vertical, rng)
        labels.append(_box_to_yolo(5, arrow_box))
        counts[5] += 1

    if rng.random() < 0.35:
        noise = rng.normalvariate(0, 2.0)
        image = cv2.convertScaleAbs(image, alpha=1.0, beta=noise)
    return image, labels, counts


def generate_split(
    root: Path,
    split: str,
    count: int,
    rng: random.Random,
    start_index: int,
) -> Counter[int]:
    image_dir = root / "images" / split
    label_dir = root / "labels" / split
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    totals: Counter[int] = Counter()
    for offset in range(count):
        index = start_index + offset
        image, labels, counts = _generate_image(rng, index)
        name = f"synthetic_{index:04d}"
        if not cv2.imwrite(str(image_dir / f"{name}.png"), image):
            raise RuntimeError(f"Não foi possível gravar {name}.png")
        (label_dir / f"{name}.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")
        totals.update(counts)
    return totals


def main() -> int:
    args = build_parser().parse_args()
    if min(args.train, args.val, args.test) <= 0:
        raise ValueError("As três divisões precisam conter ao menos uma imagem")
    rng = random.Random(args.seed)
    totals: Counter[int] = Counter()
    start = 0
    for split, count in (("train", args.train), ("val", args.val), ("test", args.test)):
        totals.update(generate_split(args.output, split, count, rng, start))
        start += count
    print(f"dataset={args.output.resolve()}")
    print(f"images={start} train={args.train} val={args.val} test={args.test}")
    print("objects=" + ", ".join(f"{CLASS_NAMES[i]}:{totals[i]}" for i in range(len(CLASS_NAMES))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
