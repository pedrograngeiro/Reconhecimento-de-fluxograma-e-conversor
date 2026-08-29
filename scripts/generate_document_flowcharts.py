"""Generate labelled document-style flowcharts for YOLO fine-tuning.

The images intentionally resemble compact exported diagrams: portrait pages,
small grey nodes, thin black outlines, Portuguese labels and side branches.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import random

import cv2
import numpy as np


WIDTH = 640
HEIGHT = 960
CLASS_NAMES = (
    "process",
    "decision",
    "terminator",
    "input_output",
    "connector",
    "arrow_head",
)
TEXTS = {
    0: ("Acordar", "Tomar cafe", "Almocar", "Passear", "Jantar", "Dormir", "Processar"),
    1: ("Dia de sol?", "Cansado?", "Aprovado?", "Continuar?", "Dados validos?"),
    2: ("Inicio", "Fim"),
    3: ("Ler dados", "Mostrar resultado", "Receber valor", "Salvar arquivo"),
    4: ("A", "B", "1", "2"),
}


@dataclass(frozen=True, slots=True)
class Shape:
    class_id: int
    box: tuple[int, int, int, int]

    @property
    def center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.box
        return ((x1 + x2) // 2, (y1 + y2) // 2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("flow-chart-document"))
    parser.add_argument("--train", type=int, default=160)
    parser.add_argument("--val", type=int, default=32)
    parser.add_argument("--test", type=int, default=32)
    parser.add_argument("--seed", type=int, default=2026)
    return parser


def _to_yolo(class_id: int, box: tuple[int, int, int, int]) -> str:
    x1, y1, x2, y2 = box
    return (
        f"{class_id} {((x1 + x2) / 2) / WIDTH:.6f} "
        f"{((y1 + y2) / 2) / HEIGHT:.6f} "
        f"{(x2 - x1) / WIDTH:.6f} {(y2 - y1) / HEIGHT:.6f}"
    )


def _text_lines(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:2]


def _draw_text(image: np.ndarray, text: str, box: tuple[int, int, int, int], rng: random.Random) -> None:
    x1, y1, x2, y2 = box
    font = rng.choice((cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX))
    scale = rng.uniform(0.38, 0.48)
    thickness = rng.choice((1, 1, 2))
    lines = _text_lines(text, max(8, int((x2 - x1) / 10)))
    sizes = [cv2.getTextSize(line, font, scale, thickness)[0] for line in lines]
    line_height = max(size[1] for size in sizes) + 5
    first_baseline = (y1 + y2 - line_height * (len(lines) - 1)) // 2
    for index, (line, size) in enumerate(zip(lines, sizes, strict=True)):
        origin = ((x1 + x2 - size[0]) // 2, first_baseline + index * line_height)
        cv2.putText(image, line, origin, font, scale, (20, 20, 20), thickness, cv2.LINE_AA)


def _rounded_rectangle(
    image: np.ndarray,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
    thickness: int,
) -> None:
    x1, y1, x2, y2 = box
    radius = min((y2 - y1) // 2, 24)
    cv2.rectangle(image, (x1 + radius, y1), (x2 - radius, y2), fill, -1)
    cv2.rectangle(image, (x1, y1 + radius), (x2, y2 - radius), fill, -1)
    cv2.circle(image, (x1 + radius, y1 + radius), radius, fill, -1)
    cv2.circle(image, (x2 - radius, y1 + radius), radius, fill, -1)
    cv2.line(image, (x1 + radius, y1), (x2 - radius, y1), outline, thickness, cv2.LINE_AA)
    cv2.line(image, (x1 + radius, y2), (x2 - radius, y2), outline, thickness, cv2.LINE_AA)
    cv2.line(image, (x1, y1 + radius), (x1, y2 - radius), outline, thickness, cv2.LINE_AA)
    cv2.line(image, (x2, y1 + radius), (x2, y2 - radius), outline, thickness, cv2.LINE_AA)
    cv2.ellipse(image, (x1 + radius, y1 + radius), (radius, radius), 0, 90, 270, outline, thickness, cv2.LINE_AA)
    cv2.ellipse(image, (x2 - radius, y1 + radius), (radius, radius), 0, 270, 450, outline, thickness, cv2.LINE_AA)


def _make_shape(class_id: int, center: tuple[int, int], rng: random.Random) -> Shape:
    cx, cy = center
    if class_id == 1:
        width, height = rng.randint(138, 170), rng.randint(76, 94)
    elif class_id == 4:
        width = height = rng.randint(34, 44)
    else:
        width, height = rng.randint(138, 178), rng.randint(42, 56)
    return Shape(class_id, (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2))


def _draw_shape(image: np.ndarray, shape: Shape, rng: random.Random) -> None:
    x1, y1, x2, y2 = shape.box
    shade = rng.randint(190, 224)
    fill = (shade, shade, shade)
    outline_value = rng.randint(20, 55)
    outline = (outline_value, outline_value, outline_value)
    thickness = rng.choice((1, 1, 2))

    if shape.class_id == 0:
        cv2.rectangle(image, (x1, y1), (x2, y2), fill, -1)
        cv2.rectangle(image, (x1, y1), (x2, y2), outline, thickness, cv2.LINE_AA)
    elif shape.class_id == 1:
        cx, cy = shape.center
        points = np.array([(cx, y1), (x2, cy), (cx, y2), (x1, cy)], dtype=np.int32)
        cv2.fillPoly(image, [points], fill)
        cv2.polylines(image, [points], True, outline, thickness, cv2.LINE_AA)
    elif shape.class_id == 2:
        _rounded_rectangle(image, shape.box, fill, outline, thickness)
    elif shape.class_id == 3:
        slant = min(22, (x2 - x1) // 6)
        points = np.array([(x1 + slant, y1), (x2, y1), (x2 - slant, y2), (x1, y2)], dtype=np.int32)
        cv2.fillPoly(image, [points], fill)
        cv2.polylines(image, [points], True, outline, thickness, cv2.LINE_AA)
    else:
        cx, cy = shape.center
        radius = (x2 - x1) // 2
        cv2.circle(image, (cx, cy), radius, fill, -1)
        cv2.circle(image, (cx, cy), radius, outline, thickness, cv2.LINE_AA)

    _draw_text(image, rng.choice(TEXTS[shape.class_id]), shape.box, rng)


def _anchor(shape: Shape, side: str) -> tuple[int, int]:
    x1, y1, x2, y2 = shape.box
    return {
        "top": ((x1 + x2) // 2, y1),
        "bottom": ((x1 + x2) // 2, y2),
        "left": (x1, (y1 + y2) // 2),
        "right": (x2, (y1 + y2) // 2),
    }[side]


def _draw_arrow(image: np.ndarray, points: list[tuple[int, int]], rng: random.Random) -> tuple[int, int, int, int]:
    color_value = rng.randint(15, 50)
    color = (color_value, color_value, color_value)
    thickness = rng.choice((1, 2))
    tip = np.array(points[-1], dtype=np.float64)
    previous = np.array(points[-2], dtype=np.float64)
    direction = tip - previous
    direction /= max(float(np.linalg.norm(direction)), 1.0)
    perpendicular = np.array((-direction[1], direction[0]))
    length = rng.randint(9, 13)
    half_width = rng.randint(5, 8)
    base = tip - direction * length
    line_points = [*points[:-1], tuple(np.rint(base).astype(int))]
    cv2.polylines(image, [np.array(line_points, dtype=np.int32)], False, color, thickness, cv2.LINE_AA)
    triangle = np.array(
        [tip, base + perpendicular * half_width, base - perpendicular * half_width],
        dtype=np.int32,
    )
    cv2.fillPoly(image, [triangle], color)
    x_values = triangle[:, 0]
    y_values = triangle[:, 1]
    return (int(x_values.min()), int(y_values.min()), int(x_values.max()), int(y_values.max()))


def generate_image(rng: random.Random, image_index: int) -> tuple[np.ndarray, list[str], Counter[int]]:
    background = rng.randint(248, 255)
    image = np.full((HEIGHT, WIDTH, 3), background, dtype=np.uint8)
    main_x = WIDTH // 2 + rng.randint(-18, 18)
    left_x = rng.randint(92, 125)
    right_x = rng.randint(515, 548)
    ys = [45, 125, 205, 300, 425, 535, 660, 755, 835, 920]
    ys = [value + rng.randint(-5, 5) for value in ys]

    main_classes = [2, 0, rng.choice((0, 3)), 1, 0, 1, 0, rng.choice((0, 3)), 0, 2]
    main = [_make_shape(class_id, (main_x + rng.randint(-12, 12), y), rng) for class_id, y in zip(main_classes, ys, strict=True)]
    first_sides = [_make_shape(rng.choice((0, 0, 3)), (left_x, ys[3]), rng), _make_shape(rng.choice((0, 0, 3)), (right_x, ys[3]), rng)]
    second_sides = [_make_shape(rng.choice((0, 0, 4)), (left_x, ys[5]), rng), _make_shape(rng.choice((0, 0, 4)), (right_x, ys[5]), rng)]
    shapes = [*main, *first_sides, *second_sides]

    arrow_boxes: list[tuple[int, int, int, int]] = []
    for source, target in zip(main[:3], main[1:4], strict=True):
        arrow_boxes.append(_draw_arrow(image, [_anchor(source, "bottom"), _anchor(target, "top")], rng))

    def draw_branch(decision: Shape, sides: list[Shape], merge: Shape) -> None:
        left, right = sides
        arrow_boxes.append(_draw_arrow(image, [_anchor(decision, "left"), _anchor(left, "right")], rng))
        arrow_boxes.append(_draw_arrow(image, [_anchor(decision, "right"), _anchor(right, "left")], rng))
        merge_y = merge.center[1]
        left_start = _anchor(left, "bottom")
        right_start = _anchor(right, "bottom")
        arrow_boxes.append(_draw_arrow(image, [left_start, (left_start[0], merge_y), _anchor(merge, "left")], rng))
        arrow_boxes.append(_draw_arrow(image, [right_start, (right_start[0], merge_y), _anchor(merge, "right")], rng))
        cv2.putText(image, rng.choice(("SIM", "NAO")), (left.box[2] + 7, decision.center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (20, 20, 20), 1, cv2.LINE_AA)
        cv2.putText(image, rng.choice(("SIM", "NAO")), (decision.box[2] + 7, decision.center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (20, 20, 20), 1, cv2.LINE_AA)

    draw_branch(main[3], first_sides, main[4])
    arrow_boxes.append(_draw_arrow(image, [_anchor(main[4], "bottom"), _anchor(main[5], "top")], rng))
    draw_branch(main[5], second_sides, main[6])
    for source, target in zip(main[6:-1], main[7:], strict=True):
        arrow_boxes.append(_draw_arrow(image, [_anchor(source, "bottom"), _anchor(target, "top")], rng))

    for shape in shapes:
        _draw_shape(image, shape, rng)

    if image_index % 3 == 0:
        noise = np.random.default_rng(rng.randrange(2**32)).normal(0, rng.uniform(0.4, 1.6), image.shape)
        image = np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    if image_index % 5 == 0:
        image = cv2.GaussianBlur(image, (3, 3), rng.uniform(0.1, 0.45))

    labels = [_to_yolo(shape.class_id, shape.box) for shape in shapes]
    labels.extend(_to_yolo(5, box) for box in arrow_boxes)
    counts = Counter(shape.class_id for shape in shapes)
    counts[5] = len(arrow_boxes)
    return image, labels, counts


def _write_split(root: Path, split: str, count: int, rng: random.Random, start: int) -> Counter[int]:
    image_dir = root / "images" / split
    label_dir = root / "labels" / split
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    totals: Counter[int] = Counter()
    for offset in range(count):
        index = start + offset
        image, labels, counts = generate_image(rng, index)
        stem = f"document_{index:04d}"
        if not cv2.imwrite(str(image_dir / f"{stem}.png"), image):
            raise RuntimeError(f"Could not write {stem}.png")
        (label_dir / f"{stem}.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")
        totals.update(counts)
    return totals


def _write_yaml(root: Path) -> None:
    names = "\n".join(f"  {index}: {name}" for index, name in enumerate(CLASS_NAMES))
    (root / "data.yaml").write_text(
        f"path: {root.resolve()}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n{names}\n",
        encoding="utf-8",
    )


def main() -> int:
    args = build_parser().parse_args()
    if min(args.train, args.val, args.test) <= 0:
        raise ValueError("All splits must contain at least one image")
    rng = random.Random(args.seed)
    totals: Counter[int] = Counter()
    start = 0
    for split, count in (("train", args.train), ("val", args.val), ("test", args.test)):
        totals.update(_write_split(args.output, split, count, rng, start))
        start += count
    _write_yaml(args.output)
    print(f"dataset={args.output.resolve()}")
    print(f"images={start} train={args.train} val={args.val} test={args.test}")
    print("objects=" + ", ".join(f"{CLASS_NAMES[index]}:{totals[index]}" for index in range(len(CLASS_NAMES))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
