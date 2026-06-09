# UI Scenario Tests

This directory includes UI scenario tests that validate key interaction flows and can refresh screenshots.
Current scenarios use `wx.UIActionSimulator` for user-like typing/clicking on the Connection Dialog.

## Scenarios

- `test_scenario_a_connection_dialog_root_flow`
  - Create and save a root connection
  - Update connection values and save again
  - Create and delete a root directory
  - Delete the root connection and verify cleanup

- `test_scenario_b_connection_dialog_nested_flow`
  - Create a directory
  - Keep nested directory selected and expanded
  - Persist expanded directory path in settings
  - Create and save a connection inside that directory
  - Rename and update the nested connection
  - Create a third connection and enable **Use SSH Tunnel** (SSH panel visible)
  - Optional final screenshot (`connection_dialog_configured.png`)
  - Optional SSH screenshot (`connection_dialog_ssh_tunnel.png`)

## Run in test mode

Use the project test runner with the dedicated UI suite:

```bash
PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:$PATH" xvfb-run -a uv run ./scripts/runtest.py --suite ui
```

The UI suite is forced to run with xdist single worker (`-n 1`) inside `scripts/runtest.py` for clearer one-failure-at-a-time diagnostics.

## Refresh screenshots

Use the same suite with `--refresh-screenshots`:

```bash
PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:$PATH" xvfb-run -a uv run ./scripts/runtest.py --suite ui --refresh-screenshots
```

Generated files are saved under `screenshot/`.
