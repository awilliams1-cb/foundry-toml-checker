# foundry-toml-checker

A GitHub Action (and standalone script) that validates `foundry.toml` against project compiler requirements.

## Checks

- `via_ir` must not be `true` in any profile
- `optimizer_details.via_ir` must not be `true` in any profile
- `solc` or `solc_version` must be set in `[profile.default]`
- `evm_version` must be set in `[profile.default]`

## Usage as a GitHub Action

Add to your workflow:

```yaml
name: Validate Foundry Config

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  check-foundry-toml:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: awilliams1-cb/foundry-toml-checker@<commit_sha>
```

The action always checks `foundry.toml` at the root of the repository.

## Usage as a standalone script

```bash
# With uv (handles dependencies automatically)
uv run check_config.py

# With pip
pip install tomli
python check_config.py
```

Exit code `0` = passed, `1` = failed or error.
