import json
from pathlib import Path

from flowchart_converter.models import SYMBOL_KINDS


def test_json_schema_matches_model_symbol_taxonomy() -> None:
    schema_path = Path("schemas/flowchart-1.1.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["properties"]["schema_version"]["const"] == "1.1"
    assert set(schema["$defs"]["node"]["properties"]["type"]["enum"]) == set(
        SYMBOL_KINDS
    )
    assert schema["$defs"]["node"]["required"] == ["id", "type"]
