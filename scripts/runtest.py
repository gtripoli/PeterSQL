#!/usr/bin/env python3
"""
Unified test runner
By default: runs unit tests only (excludes integration tests)
With --all: runs ALL tests (unit + integration)
With --update: runs ALL tests (unit + integration) and updates README badges
"""

import argparse
import subprocess
import os
import re
import sys

# Add project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from structures.connection import ConnectionEngine

README = "README.md"
TESTS_DIR = "tests/engines"
RESULTS_FILE = "/tmp/pytest_results.txt"


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
                    ['uv', 'run', 'pytest', 'tests/', '--tb=no'],
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
