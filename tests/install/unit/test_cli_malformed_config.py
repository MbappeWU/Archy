"""CLI handles malformed user configs as actionable errors without tracebacks (#590)."""

from __future__ import annotations

from click.testing import CliRunner

from archy.cli import main


def test_install_rejects_non_object_json_config(simulate_os):
    fake = simulate_os("linux")
    bad_file = fake.home / ".claude.json"
    bad_file.write_text("[]\n", encoding="utf-8")
    assert bad_file.read_text(encoding="utf-8") == "[]\n"

    result = CliRunner().invoke(main, ["install", "--target", "claude", "-y"])

    assert result.exit_code == 1
    assert str(bad_file) in result.output
    assert "expected a JSON object at the top level" in result.output
    assert "Traceback" not in result.output


def test_install_rejects_malformed_json_config(simulate_os):
    fake = simulate_os("linux")
    bad_file = fake.home / ".cursor" / "mcp.json"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_text("{ not json\n", encoding="utf-8")
    assert bad_file.read_text(encoding="utf-8") == "{ not json\n"

    result = CliRunner().invoke(main, ["install", "--target", "cursor", "-y"])

    assert result.exit_code == 1
    assert str(bad_file) in result.output
    assert "JSON decode error" in result.output
    assert "line 1 column 3" in result.output
    assert "Traceback" not in result.output


def test_install_rejects_malformed_toml_config(simulate_os):
    fake = simulate_os("linux")
    bad_file = fake.home / ".codex" / "config.toml"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_text("[[[\n", encoding="utf-8")
    assert bad_file.read_text(encoding="utf-8") == "[[[\n"

    result = CliRunner().invoke(main, ["install", "--target", "codex", "-y"])

    assert result.exit_code == 1
    assert str(bad_file) in result.output
    assert "TOML decode error" in result.output
    assert "line 1, column 3" in result.output
    assert "Traceback" not in result.output


def test_install_rejects_config_path_that_is_a_directory(simulate_os):
    fake = simulate_os("linux")
    bad_dir = fake.home / ".claude.json"
    bad_dir.mkdir(parents=True, exist_ok=True)
    assert bad_dir.is_dir()

    result = CliRunner().invoke(main, ["install", "--target", "claude", "-y"])

    assert result.exit_code == 1
    assert str(bad_dir) in result.output
    assert "is a directory" in result.output
    assert "Traceback" not in result.output


def test_uninstall_rejects_malformed_config(simulate_os):
    fake = simulate_os("linux")
    bad_file = fake.home / ".cursor" / "mcp.json"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_text("{ not json\n", encoding="utf-8")
    assert bad_file.read_text(encoding="utf-8") == "{ not json\n"

    result = CliRunner().invoke(main, ["uninstall", "--target", "cursor", "-y"])

    assert result.exit_code == 1
    assert str(bad_file) in result.output
    assert "JSON decode error" in result.output
    assert "Traceback" not in result.output
