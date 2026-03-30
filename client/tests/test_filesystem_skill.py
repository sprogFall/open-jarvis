import pytest

from client.skills.filesystem import FileSystemSkill


def test_filesystem_skill_reads_file_within_allowed_root(tmp_path):
    allowed_root = tmp_path / "data"
    allowed_root.mkdir()
    target = allowed_root / "agent.log"
    target.write_text("hello gateway", encoding="utf-8")

    skill = FileSystemSkill([allowed_root])

    assert skill.read_file(str(target)) == "hello gateway"


def test_filesystem_skill_rejects_path_outside_allowed_root(tmp_path):
    allowed_root = tmp_path / "data"
    allowed_root.mkdir()
    forbidden = tmp_path / "secrets.txt"
    forbidden.write_text("token=abc", encoding="utf-8")
    skill = FileSystemSkill([allowed_root])

    with pytest.raises(PermissionError):
        skill.read_file(str(forbidden))
