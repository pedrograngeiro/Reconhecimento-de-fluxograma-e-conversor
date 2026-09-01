"""Baixa o FC-Detection e converte suas caixas COCO para YOLO.

Fonte: https://huggingface.co/datasets/galirage/FC-Detection
Licenca do dataset: Apache-2.0
"""

from __future__ import annotations

import json
import shutil
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path


REPOSITORY = "https://huggingface.co/datasets/galirage/FC-Detection/resolve/main"
OUTPUT = Path(__file__).resolve().parent / "flow-chart"
SOURCES = {
    "source_train": "data_coco_format_start_end_train",
    "source_test": "data_coco_format_start_end_test",
}
CLASS_MAP = {
    "process": 0,
    "decision": 1,
    "terminator": 2,
    "data": 3,
    "connection": 4,
    "arrow_end": 5,
}
CLASS_NAMES = [
    "process",
    "decision",
    "terminator",
    "input_output",
    "connector",
    "arrow_head",
]


def download(relative_path: str, destination: Path) -> None:
    if destination.is_file() and destination.stat().st_size:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = f"{REPOSITORY}/{urllib.parse.quote(relative_path, safe='/')}?download=true"
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "flowchart-dataset-setup"})
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output)
    partial.replace(destination)


def split_for_train_image(index: int) -> str:
    # Ordenacao por nome + um item em cada cinco produz uma divisao reproduzivel 80/20.
    return "val" if index % 5 == 0 else "train"


def convert_source(source_name: str, source_directory: str) -> Counter[str]:
    annotation_relative = f"{source_directory}/annotations/instances_custom.json"
    annotation_path = OUTPUT / "source_annotations" / f"{source_name}.json"
    download(annotation_relative, annotation_path)

    document = json.loads(annotation_path.read_text(encoding="utf-8"))
    categories = {category["id"]: category["name"] for category in document["categories"]}
    annotations_by_image: dict[int, list[dict]] = defaultdict(list)
    for annotation in document["annotations"]:
        annotations_by_image[annotation["image_id"]].append(annotation)

    counts: Counter[str] = Counter()
    images = sorted(document["images"], key=lambda item: item["file_name"])
    for index, image in enumerate(images):
        split = "test" if source_name == "source_test" else split_for_train_image(index)
        filename = image["file_name"]
        image_relative = f"{source_directory}/images/{filename}"
        image_path = OUTPUT / "images" / split / filename
        label_path = OUTPUT / "labels" / split / f"{Path(filename).stem}.txt"
        download(image_relative, image_path)

        width = float(image["width"])
        height = float(image["height"])
        labels: list[str] = []
        for annotation in annotations_by_image[image["id"]]:
            source_class = categories[annotation["category_id"]]
            class_id = CLASS_MAP.get(source_class)
            if class_id is None:
                continue
            x, y, box_width, box_height = map(float, annotation["bbox"])
            center_x = min(1.0, max(0.0, (x + box_width / 2) / width))
            center_y = min(1.0, max(0.0, (y + box_height / 2) / height))
            normalized_width = min(1.0, max(0.0, box_width / width))
            normalized_height = min(1.0, max(0.0, box_height / height))
            labels.append(
                f"{class_id} {center_x:.8f} {center_y:.8f} "
                f"{normalized_width:.8f} {normalized_height:.8f}"
            )
            counts[CLASS_NAMES[class_id]] += 1

        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.write_text("\n".join(labels) + ("\n" if labels else ""), encoding="utf-8")
        counts[f"images_{split}"] += 1
    return counts


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    total: Counter[str] = Counter()
    for source_name, source_directory in SOURCES.items():
        total.update(convert_source(source_name, source_directory))

    dataset_path = OUTPUT.resolve().as_posix()
    names_yaml = "\n".join(f"  {index}: {name}" for index, name in enumerate(CLASS_NAMES))
    (OUTPUT / "data.yaml").write_text(
        f"path: {dataset_path}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        f"{names_yaml}\n",
        encoding="utf-8",
    )
    (OUTPUT / "SOURCE.md").write_text(
        "# Origem do dataset\n\n"
        "FC-Detection, Galirage Inc.: "
        "https://huggingface.co/datasets/galirage/FC-Detection\n\n"
        "Licenca declarada pela fonte: Apache-2.0. Foram mantidas somente as "
        "classes necessarias ao detector deste projeto. `arrow_end` foi mapeada "
        "para `arrow_head`; `data` para `input_output`; e `connection` para "
        "`connector`. As classes `text`, `arrow` e `arrow_start` foram ignoradas.\n",
        encoding="utf-8",
    )

    print(f"Dataset preparado em: {OUTPUT}")
    for key in sorted(total):
        print(f"{key}: {total[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
