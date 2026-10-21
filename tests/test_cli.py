# SPDX-FileCopyrightText: 2026 Sanath
# SPDX-License-Identifier: Apache-2.0
# SPDX-PackageName: rai-toolkit

from pathlib import Path

import pytest

from rai_toolkit.cli import main


def test_datasets_list_reports_registered_datasets(capsys) -> None:
    exit_code = main(["datasets", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "bbq" in output
    assert "halueval-qa" in output
    assert "MIT-1.1" in output


def test_demo_datasets_filters_to_requested_preset(capsys) -> None:
    exit_code = main(["datasets", "demo-datasets", "--preset", "hr"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "hr" in output
    assert "bbq" in output
    assert "bold" in output
    assert "healthcare" not in output


def test_redteam_catalog_reports_known_template(capsys) -> None:
    exit_code = main(["redteam", "catalog"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "jb-dan-classic" in output
    assert "jailbreak" in output


def test_policies_lint_accepts_valid_policy_directory(tmp_path: Path, capsys) -> None:
    (tmp_path / "valid.yaml").write_text(
        """\
name: Test policy set
version: "1.0.0"
policies:
  - name: block-secret
    description: Block secret output
    severity: high
    trigger:
      output_contains: [secret]
""",
        encoding="utf-8",
    )

    exit_code = main(["policies", "lint", str(tmp_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "OK: 1 policies loaded" in output
    assert "block-secret" in output


def test_policies_lint_rejects_invalid_policy_directory(tmp_path: Path, capsys) -> None:
    (tmp_path / "invalid.yaml").write_text(
        """\
name: Test policy set
policies:
  - name: invalid policy name
    description: Invalid policy
    trigger: {}
""",
        encoding="utf-8",
    )

    exit_code = main(["policies", "lint", str(tmp_path)])

    error = capsys.readouterr().err
    assert exit_code == 1
    assert error.startswith("FAIL:")


def test_datasets_parser_error_exits_with_code_two(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["datasets", "unknown-command"])

    assert error.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_datasets_show_unknown_exits_with_code_two_and_suggestion(capsys) -> None:
    exit_code = main(["datasets", "show", "bbqq"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Example dataset 'bbqq' not registered." in captured.err
    assert "Did you mean: bbq?" in captured.err
    assert "Traceback" not in captured.err


def test_datasets_show_unknown_no_suggestion(capsys) -> None:
    exit_code = main(["datasets", "show", "completely-unknown-xyz"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Example dataset 'completely-unknown-xyz' not registered." in captured.err
    assert "Did you mean:" not in captured.err
    assert "Traceback" not in captured.err


def test_datasets_show_known_succeeds(capsys) -> None:
    exit_code = main(["datasets", "show", "bbq"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "bbq" in captured.out
    assert captured.err == ""


def test_datasets_infer_unknown_exits_with_code_two(capsys) -> None:
    exit_code = main(["datasets", "infer-policy-expectations", "bbqq", "--limit", "0"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Example dataset 'bbqq' not registered." in captured.err
    assert "Did you mean: bbq?" in captured.err
    assert "Traceback" not in captured.err


def test_datasets_infer_known_empty_limit(capsys) -> None:
    exit_code = main(["datasets", "infer-policy-expectations", "bbq", "--limit", "0"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "[]"
    assert captured.err == ""


def test_loader_keyerror_not_treated_as_unknown_dataset(monkeypatch, capsys) -> None:
    # Simulate a KeyError from inside the loader for a registered dataset.
    # It must not be swallowed as an "unknown dataset" error.
    from rai_toolkit.examples import ExampleRegistry

    original_load = ExampleRegistry.load

    def raising_load(slug: str, limit: int | None = None):
        if slug == "bbq":
            raise KeyError("internal loader failure")
        return original_load(slug, limit)

    monkeypatch.setattr(ExampleRegistry, "load", raising_load)

    with pytest.raises(KeyError, match="internal loader failure"):
        main(["datasets", "infer-policy-expectations", "bbq", "--limit", "0"])
