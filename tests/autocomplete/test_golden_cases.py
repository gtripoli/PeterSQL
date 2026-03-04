from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import pytest

from tests.autocomplete.autocomplete_adapter import (
    AVAILABLE_ENGINES,
    AutocompleteRequest,
    get_suggestions,
)


ROOT = Path(__file__).resolve().parent
CASES_DIR = ROOT / "cases"
CONFIG_PATH = ROOT / "test_config.json"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_cases() -> Iterable[Tuple[str, Dict[str, Any]]]:
    for path in sorted(CASES_DIR.glob("*.json")):
        payload = _load_json(path)
        for case in payload["cases"]:
            yield (path.name, case)


def _schema_for_variant(config: Dict[str, Any], schema_variant: str) -> Dict[str, Any]:
    if schema_variant == "small":
        return config["schema_small"]
    if schema_variant == "big":
        return config["schema_big"]
    raise ValueError(f"Unknown schema_variant: {schema_variant}")


@pytest.mark.parametrize("engine", AVAILABLE_ENGINES)
@pytest.mark.parametrize("file_name,case", list(_iter_cases()))
def test_golden_case(file_name: str, case: Dict[str, Any], engine: str) -> None:
    config = _load_json(CONFIG_PATH)
    expected = case["expected"]

    if bool(expected.get("xfail", False)):
        pytest.xfail("Marked as future enhancement")

    schema = _schema_for_variant(config, case.get("schema_variant", "small"))

    request = AutocompleteRequest(
        sql=case["sql"],
        dialect=case.get("dialect", "generic"),
        current_table=case.get("current_table"),
        schema=schema,
        engine=engine,
    )

    response = get_suggestions(request)

    assert response.mode == expected["mode"], (file_name, case["case_id"], engine)
    assert response.context == expected["context"], (file_name, case["case_id"], engine)
    assert response.prefix == expected.get("prefix"), (
        file_name,
        case["case_id"],
        engine,
    )

    if "suggestions" in expected:
        assert response.suggestions == expected["suggestions"], (
            file_name,
            case["case_id"],
            engine,
        )
    elif "suggestions_contains" in expected and "suggestions_not_contains" in expected:
        for needle in expected["suggestions_contains"]:
            assert needle in response.suggestions, (
                file_name,
                case["case_id"],
                engine,
                needle,
            )
        for needle in expected["suggestions_not_contains"]:
            assert needle not in response.suggestions, (
                file_name,
                case["case_id"],
                engine,
                needle,
            )
    else:
        raise AssertionError(
            "Case must define 'suggestions' OR both 'suggestions_contains' AND 'suggestions_not_contains'"
        )
