from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

from client.skill_runtime import SkillWorkspaceManager


def _build_skill_archive(skill_id: str, *, root: str) -> bytes:
    archive = io.BytesIO()
    prefix = f"{root.strip('/')}/"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(
            f"{prefix}SKILL.md",
            (
                "---\n"
                f"name: {skill_id}\n"
                "description: Test skill\n"
                "---\n\n"
                "Runbook.\n"
            ),
        )
        bundle.writestr(f"{prefix}references/guide.md", "# Guide\n")
    return archive.getvalue()


def _manifest(skill_id: str, archive: bytes, **overrides) -> dict:
    payload = {
        "skill_id": skill_id,
        "config": {"workspace": ".codex/skills"},
        "skill_config": {"mode": "strict"},
        "archive_ready": True,
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "download_path": f"/client/skills/{skill_id}/archive",
    }
    payload.update(overrides)
    return payload


def test_skill_workspace_sync_downloads_extracts_and_writes_metadata(tmp_path):
    archive = _build_skill_archive("incident-kit", root="repo/skills/incident-kit")
    downloads: list[str] = []
    workspace = SkillWorkspaceManager(
        workspace_root=tmp_path / "skills-runtime",
        archive_fetcher=lambda skill: downloads.append(skill["skill_id"]) or archive,
    )

    workspace.sync([_manifest("incident-kit", archive)])

    skill_root = tmp_path / "skills-runtime" / "incident-kit"
    assert downloads == ["incident-kit"]
    assert (skill_root / "SKILL.md").exists()
    assert (skill_root / "references" / "guide.md").exists()
    assert not (skill_root / "repo").exists()
    metadata = json.loads((skill_root / ".open-jarvis-skill.json").read_text(encoding="utf-8"))
    assert metadata["skill_id"] == "incident-kit"
    assert metadata["archive_sha256"] == hashlib.sha256(archive).hexdigest()
    assert metadata["assignment_config"] == {"workspace": ".codex/skills"}
    assert metadata["skill_config"] == {"mode": "strict"}


def test_skill_workspace_sync_skips_reinstall_when_archive_is_unchanged(tmp_path):
    archive = _build_skill_archive("incident-kit", root="incident-kit")
    downloads: list[str] = []
    workspace = SkillWorkspaceManager(
        workspace_root=tmp_path / "skills-runtime",
        archive_fetcher=lambda skill: downloads.append(skill["skill_id"]) or archive,
    )
    manifest = _manifest("incident-kit", archive)

    workspace.sync([manifest])
    workspace.sync([manifest])

    assert downloads == ["incident-kit"]


def test_skill_workspace_sync_removes_unassigned_skill_directories(tmp_path):
    first_archive = _build_skill_archive("incident-kit", root="incident-kit")
    second_archive = _build_skill_archive("ops-kit", root="ops-kit")
    archives = {
        "incident-kit": first_archive,
        "ops-kit": second_archive,
    }
    workspace = SkillWorkspaceManager(
        workspace_root=tmp_path / "skills-runtime",
        archive_fetcher=lambda skill: archives[skill["skill_id"]],
    )

    workspace.sync([
        _manifest("incident-kit", first_archive),
        _manifest("ops-kit", second_archive),
    ])
    workspace.sync([_manifest("ops-kit", second_archive)])

    assert not (tmp_path / "skills-runtime" / "incident-kit").exists()
    assert (tmp_path / "skills-runtime" / "ops-kit").exists()


def test_skill_workspace_sync_rejects_archive_without_skill_manifest(tmp_path):
    broken = io.BytesIO()
    with zipfile.ZipFile(broken, "w") as bundle:
        bundle.writestr("incident-kit/readme.md", "missing manifest")

    workspace = SkillWorkspaceManager(
        workspace_root=tmp_path / "skills-runtime",
        archive_fetcher=lambda _skill: broken.getvalue(),
    )

    try:
        workspace.sync([_manifest("incident-kit", broken.getvalue())])
    except ValueError as exc:
        assert "SKILL.md" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected invalid skill archive to be rejected")

