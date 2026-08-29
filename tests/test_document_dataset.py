import random

from scripts.generate_document_flowcharts import CLASS_NAMES, HEIGHT, WIDTH, generate_image


def test_generated_document_flowchart_has_valid_yolo_labels() -> None:
    image, labels, counts = generate_image(random.Random(42), 0)

    assert image.shape == (HEIGHT, WIDTH, 3)
    assert len(labels) >= 20
    assert counts[0] > 0
    assert counts[1] == 2
    assert counts[2] == 2
    assert counts[5] > 0

    for label in labels:
        class_id, *coordinates = label.split()
        assert 0 <= int(class_id) < len(CLASS_NAMES)
        assert all(0 <= float(value) <= 1 for value in coordinates)
