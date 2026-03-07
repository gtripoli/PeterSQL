import json
from pathlib import Path
from typing import Any

import pytest

from tests.autocomplete.autocomplete_adapter import AutocompleteRequest
from tests.autocomplete.autocomplete_adapter import SUPPORTED_ENGINE_VERSIONS
from tests.autocomplete.autocomplete_adapter import get_suggestions


ROOT = Path(__file__).resolve().parent
CASES_DIR = ROOT / "cases"
CONFIG_PATH = ROOT / "test_config.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_cases() -> list[tuple[str, dict[str, Any]]]:
    cases: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(CASES_DIR.glob("*.json")):
        payload = _load_json(path)
        for case in payload["cases"]:
            cases.append((path.name, case))
    return cases


def _iter_engine_targets() -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for engine, versions in SUPPORTED_ENGINE_VERSIONS.items():
        for version in versions:
            targets.append((engine, version))
    return targets


def _schema_for_variant(config: dict[str, Any], schema_variant: str) -> dict[str, Any]:
    if schema_variant == "small":
        return config["schema_small"]
    if schema_variant == "big":
        return config["schema_big"]
    raise ValueError(f"Unknown schema_variant: {schema_variant}")


@pytest.mark.parametrize("engine,engine_version", _iter_engine_targets())
@pytest.mark.parametrize("file_name,case", _iter_cases())
def test_golden_case(
    file_name: str,
    case: dict[str, Any],
    engine: str,
    engine_version: str,
) -> None:
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
        engine_version=engine_version,
    )

    response = get_suggestions(request)

    assert response.mode == expected["mode"], (
        file_name,
        case["case_id"],
        engine,
        engine_version,
    )
    assert response.context == expected["context"], (
        file_name,
        case["case_id"],
        engine,
        engine_version,
    )
    assert response.prefix == expected.get("prefix"), (
        file_name,
        case["case_id"],
        engine,
        engine_version,
    )

    if "suggestions" in expected:
        assert response.suggestions == expected["suggestions"], (
            file_name,
            case["case_id"],
            engine,
            engine_version,
        )
    elif "suggestions_contains" in expected and "suggestions_not_contains" in expected:
        for needle in expected["suggestions_contains"]:
            assert needle in response.suggestions, (
                file_name,
                case["case_id"],
                engine,
                engine_version,
                needle,
            )
        for needle in expected["suggestions_not_contains"]:
            assert needle not in response.suggestions, (
                file_name,
                case["case_id"],
                engine,
                engine_version,
                needle,
            )
    else:
        raise AssertionError(
            "Case must define 'suggestions' OR both 'suggestions_contains' AND 'suggestions_not_contains'"
        )
