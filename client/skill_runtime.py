from __future__ import annotations

import hashlib
import io
import json
import shutil
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

from client.config import ClientConfig
from client.security import build_device_signature


class SkillWorkspaceManager:
    def __init__(
        self,
        *,
        workspace_root: Path,
        archive_fetcher: Callable[[dict], bytes],
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.archive_fetcher = archive_fetcher
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def sync(self, skills: list[dict]) -> None:
        archive_skills = [
            skill
            for skill in skills
            if (skill.get("source") or "archive") == "archive"
        ]
        desired_skill_ids = {skill["skill_id"] for skill in archive_skills}
        for skill in archive_skills:
            self._ensure_skill(skill)
        for child in self.workspace_root.iterdir():
            if child.is_dir() and child.name not in desired_skill_ids:
                shutil.rmtree(child)

    def _ensure_skill(self, skill: dict) -> None:
        skill_id = skill["skill_id"]
        if not skill.get("archive_ready"):
            raise ValueError(f"Skill {skill_id} 没有可用压缩包")
        archive_sha256 = skill["archive_sha256"]
        target_dir = self.workspace_root / skill_id
        metadata_path = target_dir / ".open-jarvis-skill.json"
        metadata = self._load_metadata(metadata_path)
        if metadata.get("archive_sha256") == archive_sha256 and target_dir.exists():
            self._write_metadata(target_dir, skill)
            return
        archive = self.archive_fetcher(skill)
        if hashlib.sha256(archive).hexdigest() != archive_sha256:
            raise ValueError(f"Skill {skill_id} 压缩包校验失败")
        self._install_archive(skill, archive, target_dir)

    @staticmethod
    def _load_metadata(metadata_path: Path) -> dict:
        if not metadata_path.exists():
            return {}
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _install_archive(self, skill: dict, archive: bytes, target_dir: Path) -> None:
        temp_dir = target_dir.parent / f".{target_dir.name}.tmp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
                skill_root = _detect_skill_root(bundle, skill["skill_id"])
                root_parts = skill_root.parts
                for info in bundle.infolist():
                    normalized = _normalize_member_path(info.filename)
                    if normalized is None:
                        continue
                    if root_parts:
                        try:
                            relative = normalized.relative_to(skill_root)
                        except ValueError:
                            continue
                    else:
                        relative = normalized
                    if not relative.parts:
                        continue
                    target_path = temp_dir / relative.as_posix()
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.open(info) as source, target_path.open("wb") as destination:
                        shutil.copyfileobj(source, destination)
        except zipfile.BadZipFile as exc:
            raise ValueError("Skill 压缩包必须是有效的 zip 文件") from exc
        self._write_metadata(temp_dir, skill)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        temp_dir.replace(target_dir)

    def _write_metadata(self, target_dir: Path, skill: dict) -> None:
        payload = {
            "skill_id": skill["skill_id"],
            "archive_sha256": skill["archive_sha256"],
            "assignment_config": skill.get("config") or {},
            "skill_config": skill.get("skill_config") or {},
        }
        (target_dir / ".open-jarvis-skill.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class GatewaySkillArchiveFetcher:
    def __init__(self, config: ClientConfig) -> None:
        self.config = config

    def __call__(self, skill: dict) -> bytes:
        download_path = skill.get("download_path") or f"/client/skills/{skill['skill_id']}/archive"
        timestamp = int(time.time())
        signature = build_device_signature(
            self.config.device_id,
            timestamp,
            self.config.device_key,
        )
        query = urllib.parse.urlencode(
            {
                "device_id": self.config.device_id,
                "timestamp": timestamp,
                "signature": signature,
            }
        )
        url = f"{self.config.gateway_http_url.rstrip('/')}{download_path}?{query}"
        with urllib.request.urlopen(url) as response:
            return response.read()


def _normalize_member_path(filename: str) -> PurePosixPath | None:
    raw = PurePosixPath(filename)
    if raw.is_absolute():
        raise ValueError("Skill 压缩包内路径不能是绝对路径")
    if filename.endswith("/"):
        return None
    parts = [part for part in raw.parts if part not in ("", ".")]
    if ".." in parts:
        raise ValueError("Skill 压缩包内路径不能包含 ..")
    if not parts:
        return None
    return PurePosixPath(*parts)


def _detect_skill_root(archive: zipfile.ZipFile, skill_id: str) -> PurePosixPath:
    candidates: list[PurePosixPath] = []
    for info in archive.infolist():
        normalized = _normalize_member_path(info.filename)
        if normalized is None:
            continue
        if normalized.name == "SKILL.md":
            candidates.append(normalized.parent)
    if not candidates:
        raise ValueError("Skill 压缩包内必须包含 SKILL.md")
    unique_candidates = list(dict.fromkeys(candidates))
    exact_matches = [candidate for candidate in unique_candidates if candidate.name == skill_id]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(unique_candidates) == 1:
        return unique_candidates[0]
    raise ValueError("Skill 压缩包内存在多个 SKILL.md，无法确定要安装哪个 Skill")
