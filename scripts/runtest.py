#!/usr/bin/env python3
"""
PeterSQL test runner

  (no args)                    Run all tests and update README badges
  unit                         Unit tests only (tests/core/)
  autocomplete                 Autocomplete golden-case tests
  autocomplete --engine <name> Restrict autocomplete tests to one engine
  integration                  Integration tests only
  integration --engine <name>  Restrict integration tests to one engine
  ui                           UI tests (always refreshes screenshots)
"""

import argparse
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from structures.connection import ConnectionEngine

README = "README.md"
RESULTS_FILE = "/tmp/pytest_results.txt"
JUNIT_FILE = "/tmp/pytest_results.xml"

SUITE_BADGES_START = "<!-- SUITE_BADGES_START -->"
SUITE_BADGES_END = "<!-- SUITE_BADGES_END -->"

SUITE_ORDER = ["autocomplete", "core", "ui", "mysql", "mariadb", "postgresql", "sqlite"]


# ---------------------------------------------------------------------------
# Badge helpers
# ---------------------------------------------------------------------------

def _build_suite_badges_table(suite_stats: dict[str, dict[str, int]]) -> str:
    lines = [
        SUITE_BADGES_START,
        "### Suite status (passed / skipped)",
        "",
        "| Suite | Passed | Skipped |",
        "|-------|--------|---------|",
    ]
    for suite_name in SUITE_ORDER:
        passed = suite_stats[suite_name]["passed"]
        skipped = suite_stats[suite_name]["skipped"]
        passed_badge = f"![passed](https://img.shields.io/badge/passed-{passed}-brightgreen)"
        skipped_badge = f"![skipped](https://img.shields.io/badge/skipped-{skipped}-lightgrey)"
        lines.append(f"| {suite_name} | {passed_badge} | {skipped_badge} |")
    lines += ["", SUITE_BADGES_END]
    return "\n".join(lines)


def _extract_suite_name(case_node: ET.Element) -> str:
    file_path = case_node.attrib.get("file", "")
    class_name = case_node.attrib.get("classname", "")
    source = file_path or class_name.replace(".", "/")
    mapping = [
        ("tests/autocomplete/", "autocomplete"),
        ("tests/core/", "core"),
        ("tests/ui/", "ui"),
        ("tests/engines/mysql/", "mysql"),
        ("tests/engines/mariadb/", "mariadb"),
        ("tests/engines/postgresql/", "postgresql"),
        ("tests/engines/sqlite/", "sqlite"),
    ]
    for prefix, suite_name in mapping:
        if source.startswith(prefix):
            return suite_name
    return ""


def _load_suite_stats(junit_file: str) -> dict[str, dict[str, int]]:
    stats = {name: {"passed": 0, "skipped": 0} for name in SUITE_ORDER}
    if not os.path.exists(junit_file):
        return stats
    try:
        tree = ET.parse(junit_file)
    except ET.ParseError:
        return stats
    for case in tree.getroot().findall(".//testcase"):
        suite_name = _extract_suite_name(case)
        if not suite_name:
            continue
        if case.find("skipped") is not None:
            stats[suite_name]["skipped"] += 1
        elif case.find("failure") is None and case.find("error") is None:
            stats[suite_name]["passed"] += 1
    return stats


def _extract_versions_badge(file_path: str, var_name: str) -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("conftest", file_path)
        if spec is None or spec.loader is None:
            return ""
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        versions = getattr(module, var_name, [])
        if not isinstance(versions, list):
            return ""
        versions = sorted(
            [v.split(":", 1)[1] for v in versions if ":" in v],
            key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)],
        )
        return "%20%7C%20".join(versions)
    except Exception:
        return ""


def _update_readme(results_content: str, suite_stats: dict[str, dict[str, int]]) -> None:
    if not os.path.exists(README):
        return
    try:
        with open(README) as f:
            content = f.read()

        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", results_content)
        if match:
            coverage = match.group(1)
            content = re.sub(r"coverage-\d+%", f"coverage-{coverage}%", content)
            print(f"  Coverage: {coverage}%")

        content = re.sub(
            rf"{re.escape(SUITE_BADGES_START)}.*?{re.escape(SUITE_BADGES_END)}",
            _build_suite_badges_table(suite_stats),
            content,
            flags=re.DOTALL,
        )

        for engine in ConnectionEngine:
            versions = _extract_versions_badge(
                f"tests/engines/{engine.name.lower()}/conftest.py",
                f"{engine.name.upper()}_VERSIONS",
            )
            color = "green"
            content = re.sub(
                rf"!\[{engine.value.name}\]\(https://img\.shields\.io/badge/{engine.value.name}-[^)]*\)",
                f"![{engine.value.name}](https://img.shields.io/badge/{engine.value.name}-{versions}-{color})",
                content,
            )

        with open(README, "w") as f:
            f.write(content)
        print("  README.md updated")
    except IOError as e:
        print(f"  Error updating README: {e}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _run(cmd: list[str], capture: bool = False) -> int:
    if not capture:
        return subprocess.run(cmd).returncode
    try:
        with open(RESULTS_FILE, "w") as f:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(process.stdout.readline, ""):
                print(line, end="", flush=True)
                f.write(line)
            return process.wait()
    except (IOError, OSError) as e:
        print(f"Error: {e}")
        return 1


def main() -> int:
    engine_choices = [e.value.name.lower() for e in ConnectionEngine]

    parser = argparse.ArgumentParser(
        description="PeterSQL test runner",
        epilog="Run without arguments to execute all tests and update README badges.",
    )
    sub = parser.add_subparsers(dest="suite", metavar="suite")

    sub.add_parser("unit", help="Unit tests only (tests/core/)")

    ac = sub.add_parser("autocomplete", help="Autocomplete golden-case tests")
    ac.add_argument("--engine", choices=engine_choices, help="Restrict to one engine")

    it = sub.add_parser("integration", help="Integration tests only")
    it.add_argument("--engine", choices=engine_choices, help="Restrict to one engine")

    sub.add_parser("ui", help="UI tests (always refreshes screenshots)")

    args = parser.parse_args()
    suite = args.suite
    engine = getattr(args, "engine", None)

    if suite == "unit":
        print("Running unit tests...")
        exit_code = _run([
            "uv", "run", "pytest", "tests/core/",
            "--tb=short",
        ])

    elif suite == "autocomplete":
        label = f" [{engine}]" if engine else ""
        print(f"Running autocomplete tests{label}...")
        cmd = ["uv", "run", "pytest", "tests/autocomplete/", "--tb=short"]
        if engine:
            cmd += ["-k", engine]
        exit_code = _run(cmd)

    elif suite == "integration":
        target = f"tests/engines/{engine}/" if engine else "tests/"
        label = f" [{engine}]" if engine else ""
        print(f"Running integration tests{label}...")
        exit_code = _run([
            "uv", "run", "pytest", target,
            "--tb=short", "-m", "integration", "--ignore=tests/ui",
        ])

    elif suite == "ui":
        print("Running UI tests...")
        exit_code = _run([
            "xvfb-run", "-a",
            "uv", "run", "pytest", "tests/ui/test_scenarios.py",
            "--tb=short", "-n", "1", "--refresh-screenshots",
        ])

    else:
        print("Running all tests...")
        exit_code = _run([
            "uv", "run", "pytest", "tests/",
            "--tb=no", "--ignore=tests/ui", "--junitxml", JUNIT_FILE,
        ], capture=True)

        print("\nUpdating README badges...")
        results_content = ""
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE) as f:
                results_content = f.read()
        _update_readme(results_content, _load_suite_stats(JUNIT_FILE))

        for path in (RESULTS_FILE, JUNIT_FILE):
            try:
                os.remove(path)
            except OSError:
                pass

    print(f"\nDone. Exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
