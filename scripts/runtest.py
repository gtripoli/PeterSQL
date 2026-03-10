#!/usr/bin/env python3
"""
Unified test runner
By default: runs unit tests only (excludes integration tests)
With --all: runs ALL tests (unit + integration)
With --update: runs ALL tests (unit + integration) and updates README badges
"""

import argparse
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

# Add project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from structures.connection import ConnectionEngine

README = "README.md"
TESTS_DIR = "tests/engines"
RESULTS_FILE = "/tmp/pytest_results.txt"
JUNIT_FILE = "/tmp/pytest_results.xml"

SUITE_BADGES_START = "<!-- SUITE_BADGES_START -->"
SUITE_BADGES_END = "<!-- SUITE_BADGES_END -->"

SUITE_ORDER = [
    "autocomplete",
    "core",
    "ui",
    "mysql",
    "mariadb",
    "postgresql",
    "sqlite",
]


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
    stats = {
        suite_name: {"passed": 0, "skipped": 0}
        for suite_name in SUITE_ORDER
    }

    if not os.path.exists(junit_file):
        return stats

    try:
        tree = ET.parse(junit_file)
    except ET.ParseError:
        return stats

    root = tree.getroot()
    for case in root.findall(".//testcase"):
        suite_name = _extract_suite_name(case)
        if not suite_name:
            continue

        if case.find("skipped") is not None:
            stats[suite_name]["skipped"] += 1
            continue

        if case.find("failure") is not None or case.find("error") is not None:
            continue

        stats[suite_name]["passed"] += 1

    return stats


def _update_suite_badges_block(content: str, suite_stats: dict[str, dict[str, int]]) -> str:
    replacement = _build_suite_badges_table(suite_stats)
    block_pattern = re.compile(
        rf"{re.escape(SUITE_BADGES_START)}.*?{re.escape(SUITE_BADGES_END)}",
        re.DOTALL,
    )

    if block_pattern.search(content):
        return block_pattern.sub(replacement, content)

    anchor = "For detailed test coverage matrix, statistics, and architecture, see **[tests/README.md](tests/README.md)**."
    if anchor in content:
        return content.replace(anchor, f"{anchor}\n\n{replacement}")

    return f"{content}\n\n{replacement}\n"


def get_engine_color(engine, results_content):
    """Determine color from test results for a specific engine."""
    pattern = f"tests/engines/{engine}/"

    has_passed = f"{pattern}" in results_content and "PASSED" in results_content
    has_failed = f"{pattern}" in results_content and "FAILED" in results_content

    if has_passed:
        if has_failed:
            return "orange"
        else:
            return "green"
    elif has_failed:
        return "red"
    else:
        return "lightgrey"


def extract_versions_badge(file_path, var_name):
    """Extract versions from conftest file by importing the module directly."""
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

        # Extract version strings after :
        versions = [v.split(':', 1)[1] for v in versions if ':' in v]

        # Sort versions using natural sort
        def natural_sort_key(s):
            return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

        versions.sort(key=natural_sort_key)

        # Join with |
        result = '|'.join(versions)

        # URL encode |
        result = result.replace('|', '%20%7C%20')

        return result

    except (ImportError, AttributeError, IOError, Exception):
        return ""


def update_badges():
    """Update README badges based on test results."""
    if not os.path.exists(RESULTS_FILE):
        return

    try:
        with open(RESULTS_FILE, 'r') as f:
            results_content = f.read()
    except IOError:
        return

    # Extract coverage percentage
    match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', results_content)
    coverage = match.group(1) if match else "0"

    tests_total_match = re.search(r'\[(\d+)\s+items\]', results_content)
    tests_total = tests_total_match.group(1) if tests_total_match else "unknown"
    suite_stats = _load_suite_stats(JUNIT_FILE)

    print(f"\nCoverage: {coverage}%")
    print("\nAnalyzing results for badge updates...")

    colors = {}
    for engine in ConnectionEngine:
        colors[engine] = get_engine_color(engine.value.dialect, results_content)
        print(f"  {engine.value.name}: {colors[engine]}")

    # Update README
    if os.path.exists(README):
        try:
            with open(README, 'r') as f:
                content = f.read()

            # Update coverage badge
            if coverage:
                content = re.sub(r'coverage-\d+%', f'coverage-{coverage}%', content)
                print(f"  Coverage badge updated: {coverage}%")

            # Update total tests badge
            content = re.sub(
                r'!\[Tests\]\(https://img\.shields\.io/badge/tests-[^\)]*\)',
                f'![Tests](https://img.shields.io/badge/tests-{tests_total}-blue)',
                content,
            )

            if "![Tests](https://img.shields.io/badge/tests-" not in content:
                content = re.sub(
                    r'(!\[Coverage\]\(https://img\.shields\.io/badge/coverage-[^\)]*\))',
                    rf'\1\n![Tests](https://img.shields.io/badge/tests-{tests_total}-blue)',
                    content,
                    count=1,
                )

            print(f"  Tests badge updated: {tests_total}")

            content = _update_suite_badges_block(content, suite_stats)
            print("  Suite matrix badges updated")

            # Update engine badges

            for engine, color in colors.items():
                versions = extract_versions_badge(f"tests/engines/{engine.name.lower()}/conftest.py", f'{engine.name.upper()}_VERSIONS')
                content = re.sub(
                    rf'!\[{engine.value.name}\]\(https://img.shields.io/badge/{engine.value.name}-[^)]*\)',
                    f'![{engine.value.name}](https://img.shields.io/badge/{engine.value.name}-{versions}-{color})',
                    content
                )

            with open(README, 'w') as f:
                f.write(content)

            print("\nREADME.md updated")

        except IOError as e:
            print(f"Error updating README: {e}")

    # Cleanup
    try:
        os.remove(RESULTS_FILE)
    except OSError:
        pass

    try:
        os.remove(JUNIT_FILE)
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(description='Unified test runner')
    parser.add_argument('--all', action='store_true',
                        help='Run all tests (unit + integration)')
    parser.add_argument('--update', action='store_true',
                        help='Run all tests (unit + integration) and update README badges')

    args = parser.parse_args()

    if args.all:
        print("Running ALL tests (unit + integration)...")
        result = subprocess.run(['uv', 'run', 'pytest', 'tests/', '--tb=no'])
        exit_code = result.returncode

    elif args.update:
        print("Running ALL tests (unit + integration) and updating badges...")

        # Run pytest with pipes to capture output in real-time
        try:
            with open(RESULTS_FILE, 'w') as f:
                process = subprocess.Popen(
                    [
                        'uv',
                        'run',
                        'pytest',
                        'tests/',
                        '--tb=no',
                        '--junitxml',
                        JUNIT_FILE,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

                # Read and print output in real-time
                for line in iter(process.stdout.readline, ''):
                    print(line, end='', flush=True)
                    f.write(line)

                exit_code = process.wait()

            # Now update badges
            update_badges()

        except (IOError, OSError) as e:
            print(f"Error running tests: {e}")
            exit_code = 1

    else:
        print("Running unit tests...")
        result = subprocess.run([
            'uv', 'run', 'pytest', 'tests/', '--tb=short', '-m', 'not integration'
        ])
        exit_code = result.returncode

        print(f"\nLocal tests completed")
        print("\nNote: Integration tests excluded. Run with --update for all tests with badge updates, or --all for full test suite.")

    print(f"\nDone. Pytest exit code: {exit_code}")
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
