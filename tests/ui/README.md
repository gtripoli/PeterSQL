# UI Scenario Tests

This directory includes UI scenario tests that validate key interaction flows and can refresh screenshots.

## Scenarios

- `test_scenario_connection_dialog_configured`
  - Create directory
  - Create connection
  - Save connection
  - Rename connection
  - Optional final screenshot

- `test_scenario_connection_dialog_tree_state`
  - Build a minimal connection tree state
  - Save connection
  - Optional final screenshot

## Run in test mode

Use the project test runner with the dedicated UI suite:

```bash
PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:$PATH" xvfb-run -a uv run ./scripts/runtest.py --suite ui
```

## Refresh screenshots

Use the same suite with `--refresh-screenshots`:

```bash
PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:$PATH" xvfb-run -a uv run ./scripts/runtest.py --suite ui --refresh-screenshots
```

Generated files are saved under `screenshot/`.
