#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "tomli>=2.0",
# ]
# ///

"""
Validates foundry.toml against project compiler requirements:
  - 'via_ir' must not be enabled (true) in any profile
  - 'optimizer_details.via_ir' must not be enabled (true) in any profile
  - 'solc' or 'solc_version' must be set in [profile.default]
  - 'evm_version' must be set in [profile.default]

Usage:
  uv run check_config.py

Exit codes:
  0 - validation passed
  1 - validation failed, file not found, or parse error
"""

import os
import sys
import tomli


def load_toml(path):
    with open(path, "rb") as f:
        return tomli.load(f)


def validate(config):
    errors = []
    profiles = config.get("profile", {})

    if not profiles:
        errors.append("No [profile.*] sections found in foundry.toml.")
        return errors

    # Check forbidden options across all profiles.
    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue

        # via_ir must not be enabled.
        if profile.get("via_ir") is True:
            errors.append(
                f"[profile.{profile_name}]: 'via_ir = true' is not allowed"
            )

        # via_ir must not be enabled inside optimizer_details.
        optimizer_details = profile.get("optimizer_details", {})
        if isinstance(optimizer_details, dict) and optimizer_details.get("via_ir") is True:
            errors.append(
                f"[profile.{profile_name}]: 'optimizer_details.via_ir = true' is not allowed"
            )

    # Check required options in the default profile.
    default = profiles.get("default", {})
    if not isinstance(default, dict):
        errors.append("[profile.default] section is missing or malformed.")
        return errors

    has_solc = bool(default.get("solc") or default.get("solc_version"))
    if not has_solc:
        errors.append(
            "[profile.default]: 'solc' (or 'solc_version') must be set."
        )

    if not default.get("evm_version"):
        errors.append("[profile.default]: 'evm_version' must be set.")

    return errors


def main():
    toml_path = "foundry.toml"

    if not os.path.isfile(toml_path):
        print(f"ERROR: '{toml_path}' not found.")
        sys.exit(1)

    try:
        config = load_toml(toml_path)
    except Exception as e:
        print(f"ERROR: Failed to parse '{toml_path}': {e}")
        sys.exit(1)

    errors = validate(config)

    if errors:
        print(f"foundry.toml validation FAILED ({toml_path}):")
        for err in errors:
            print(f"  FAIL: {err}")
        sys.exit(1)

    print(f"foundry.toml validation passed ({toml_path}).")
    sys.exit(0)


if __name__ == "__main__":
    main()
