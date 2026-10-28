"""A file archy cannot safely read is an InstallError, not a traceback (#543)."""

import pytest

from archy.install.writer import InstallError, RealWriteSystem


def test_a_non_utf8_file_names_the_path_and_is_left_alone(tmp_path):
    path = tmp_path / "CLAUDE.md"
    original = b"caf\xe9\n"
    path.write_bytes(original)

    with pytest.raises(InstallError, match="not valid UTF-8") as excinfo:
        RealWriteSystem().read_text(path)

    assert str(path) in str(excinfo.value)
    assert path.read_bytes() == original


def test_a_bom_prefixed_file_is_refused_not_reencoded(tmp_path):
    path = tmp_path / "settings.json"
    original = b"\xef\xbb\xbf{}\n"
    path.write_bytes(original)

    with pytest.raises(InstallError, match="UTF-8 BOM") as excinfo:
        RealWriteSystem().read_text(path)

    assert str(path) in str(excinfo.value)
    assert path.read_bytes() == original


def test_an_unreadable_file_names_the_path(tmp_path, monkeypatch):
    path = tmp_path / "CLAUDE.md"
    path.write_text("x", encoding="utf-8")

    def deny(self, *args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(type(path), "read_text", deny)

    with pytest.raises(InstallError, match="cannot read") as excinfo:
        RealWriteSystem().read_text(path)

    assert str(path) in str(excinfo.value)


def test_a_missing_file_is_still_none(tmp_path):
    assert RealWriteSystem().read_text(tmp_path / "missing.md") is None


def test_a_directory_names_the_path_and_is_refused(tmp_path):
    path = tmp_path / "CLAUDE.md"
    path.mkdir()

    with pytest.raises(InstallError, match="is a directory") as excinfo:
        RealWriteSystem().read_text(path)

    assert str(path) in str(excinfo.value)
