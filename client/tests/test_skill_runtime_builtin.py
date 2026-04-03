from __future__ import annotations

import hashlib

from client.skill_runtime import SkillWorkspaceManager
from client.tests.test_skill_runtime import _build_skill_archive, _manifest


def test_skill_workspace_sync_ignores_builtin_skills(tmp_path):
    archive = _build_skill_archive("incident-kit", root="repo/skills/incident-kit")
    downloads: list[str] = []
    workspace = SkillWorkspaceManager(
        workspace_root=tmp_path / "skills-runtime",
        archive_fetcher=lambda skill: downloads.append(skill["skill_id"]) or archive,
    )

    workspace.sync(
        [
            _manifest("incident-kit", archive),
            {
                "skill_id": "builtin-shell",
                "source": "builtin",
                "archive_ready": True,
                "archive_sha256": hashlib.sha256(b"builtin-shell").hexdigest(),
            },
        ]
    )

    assert downloads == ["incident-kit"]
    assert (tmp_path / "skills-runtime" / "incident-kit" / "SKILL.md").exists()
    assert not (tmp_path / "skills-runtime" / "builtin-shell").exists()
