import os
import pytest
from unittest.mock import patch
from check_config import validate, load_toml, main


class TestValidatePassingConfigs:
    def test_valid_config_with_solc(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                }
            }
        }
        assert validate(config) == []

    def test_valid_config_with_solc_version(self):
        config = {
            "profile": {
                "default": {
                    "solc_version": "0.8.19",
                    "evm_version": "paris",
                }
            }
        }
        assert validate(config) == []

    def test_valid_config_via_ir_false(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                    "via_ir": False,
                }
            }
        }
        assert validate(config) == []

    def test_valid_config_optimizer_details_via_ir_false(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                    "optimizer_details": {"via_ir": False},
                }
            }
        }
        assert validate(config) == []

    def test_valid_config_multiple_profiles(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                },
                "ci": {
                    "via_ir": False,
                },
            }
        }
        assert validate(config) == []


class TestValidateViaIr:
    def test_via_ir_true_in_default(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                    "via_ir": True,
                }
            }
        }
        errors = validate(config)
        assert len(errors) == 1
        assert "via_ir = true" in errors[0]
        assert "profile.default" in errors[0]

    def test_via_ir_true_in_non_default_profile(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                },
                "ci": {
                    "via_ir": True,
                },
            }
        }
        errors = validate(config)
        assert len(errors) == 1
        assert "profile.ci" in errors[0]

    def test_optimizer_details_via_ir_true(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                    "optimizer_details": {"via_ir": True},
                }
            }
        }
        errors = validate(config)
        assert len(errors) == 1
        assert "optimizer_details.via_ir = true" in errors[0]

    def test_both_via_ir_and_optimizer_details_via_ir_true(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                    "via_ir": True,
                    "optimizer_details": {"via_ir": True},
                }
            }
        }
        errors = validate(config)
        assert len(errors) == 2

    def test_via_ir_true_across_multiple_profiles(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                    "via_ir": True,
                },
                "ci": {
                    "via_ir": True,
                },
            }
        }
        errors = validate(config)
        assert len(errors) == 2


class TestValidateRequiredFields:
    def test_missing_solc_and_solc_version(self):
        config = {
            "profile": {
                "default": {
                    "evm_version": "paris",
                }
            }
        }
        errors = validate(config)
        assert len(errors) == 1
        assert "solc" in errors[0]

    def test_missing_evm_version(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                }
            }
        }
        errors = validate(config)
        assert len(errors) == 1
        assert "evm_version" in errors[0]

    def test_missing_both_solc_and_evm_version(self):
        config = {
            "profile": {
                "default": {}
            }
        }
        errors = validate(config)
        assert len(errors) == 2

    def test_no_profiles(self):
        errors = validate({})
        assert len(errors) == 1
        assert "No [profile.*] sections" in errors[0]

    def test_empty_profiles(self):
        errors = validate({"profile": {}})
        assert len(errors) == 1
        assert "No [profile.*] sections" in errors[0]

    def test_default_profile_not_a_dict(self):
        config = {"profile": {"default": "invalid"}}
        errors = validate(config)
        assert any("missing or malformed" in e for e in errors)


class TestValidateEdgeCases:
    def test_profile_value_not_a_dict_is_skipped(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                },
                "weird": "not-a-dict",
            }
        }
        assert validate(config) == []

    def test_optimizer_details_not_a_dict(self):
        config = {
            "profile": {
                "default": {
                    "solc": "0.8.19",
                    "evm_version": "paris",
                    "optimizer_details": "not-a-dict",
                }
            }
        }
        assert validate(config) == []


class TestLoadToml:
    def test_load_valid_toml(self, tmp_path):
        toml_file = tmp_path / "test.toml"
        toml_file.write_text('[profile.default]\nsolc = "0.8.19"\n')
        result = load_toml(str(toml_file))
        assert result["profile"]["default"]["solc"] == "0.8.19"

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_toml("nonexistent.toml")

    def test_load_invalid_toml(self, tmp_path):
        toml_file = tmp_path / "bad.toml"
        toml_file.write_bytes(b"[invalid toml ===")
        with pytest.raises(Exception):
            load_toml(str(toml_file))


class TestMain:
    def test_main_file_not_found(self, monkeypatch, capsys):
        monkeypatch.chdir("/tmp")
        with pytest.raises(SystemExit, match="1"):
            main()
        assert "not found" in capsys.readouterr().out

    def test_main_valid_config(self, tmp_path, monkeypatch, capsys):
        toml_file = tmp_path / "foundry.toml"
        toml_file.write_text(
            '[profile.default]\nsolc = "0.8.19"\nevm_version = "paris"\n'
        )
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit, match="0"):
            main()
        assert "passed" in capsys.readouterr().out

    def test_main_invalid_config(self, tmp_path, monkeypatch, capsys):
        toml_file = tmp_path / "foundry.toml"
        toml_file.write_text("[profile.default]\n")
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit, match="1"):
            main()
        assert "FAILED" in capsys.readouterr().out

    def test_main_parse_error(self, tmp_path, monkeypatch, capsys):
        toml_file = tmp_path / "foundry.toml"
        toml_file.write_bytes(b"[bad toml ===")
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit, match="1"):
            main()
        assert "Failed to parse" in capsys.readouterr().out
