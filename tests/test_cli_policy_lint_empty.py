# SPDX-FileCopyrightText: 2026 Sanath
# SPDX-License-Identifier: Apache-2.0
# SPDX-PackageName: rai-toolkit

from pathlib import Path

from rai_toolkit.cli import main


def test_policies_lint_fails_on_empty_directory(tmp_path: Path, capsys) -> None:
    exit_code = main(["policies", "lint", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err.startswith("FAIL:")
    assert str(tmp_path) in captured.err
    assert "*.yaml" in captured.err
    assert "OK:" not in captured.out


def test_policies_lint_fails_when_directory_has_only_unrelated_files(
    tmp_path: Path, capsys
) -> None:
    (tmp_path / "README.txt").write_text("No policy files here.\n", encoding="utf-8")

    exit_code = main(["policies", "lint", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err.startswith("FAIL:")
    assert str(tmp_path) in captured.err
    assert "*.yaml" in captured.err
    assert "OK:" not in captured.out


def test_policies_lint_accepts_valid_empty_policy_set(tmp_path: Path, capsys) -> None:
    (tmp_path / "empty.yaml").write_text(
        "name: Empty policy set\nversion: 1.0.0\npolicies: []\n",
        encoding="utf-8",
    )

    exit_code = main(["policies", "lint", str(tmp_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "OK: 0 policies loaded" in output


def test_policies_lint_accepts_disabled_only_policy_set(tmp_path: Path, capsys) -> None:
    (tmp_path / "disabled.yaml").write_text(
        "name: Disabled policy set\n"
        "version: 1.0.0\n"
        "policies:\n"
        "  - name: block-secret\n"
        "    description: Block secret output\n"
        "    severity: high\n"
        "    enabled: false\n"
        "    trigger:\n"
        "      output_contains: [secret]\n",
        encoding="utf-8",
    )

    exit_code = main(["policies", "lint", str(tmp_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "OK: 0 policies loaded" in output
    assert "block-secret" not in output


def test_policies_lint_accepts_enabled_policy(tmp_path: Path, capsys) -> None:
    (tmp_path / "valid.yaml").write_text(
        "name: Test policy set\n"
        "version: 1.0.0\n"
        "policies:\n"
        "  - name: block-secret\n"
        "    description: Block secret output\n"
        "    severity: high\n"
        "    trigger:\n"
        "      output_contains: [secret]\n",
        encoding="utf-8",
    )

    exit_code = main(["policies", "lint", str(tmp_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "OK: 1 policies loaded" in output
    assert "block-secret" in output


def test_policies_lint_rejects_invalid_policy_directory(tmp_path: Path, capsys) -> None:
    (tmp_path / "invalid.yaml").write_text(
        "name: Test policy set\n"
        "policies:\n"
        "  - name: invalid policy name\n"
        "    description: Invalid policy\n"
        "    trigger: {}\n",
        encoding="utf-8",
    )

    exit_code = main(["policies", "lint", str(tmp_path)])

    error = capsys.readouterr().err
    assert exit_code == 1
    assert error.startswith("FAIL:")
