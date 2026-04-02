from __future__ import annotations

import hashlib
import io
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(slots=True)
class SkillArchiveMetadata:
    filename: str
    sha256: str
    size: int


class SkillArchiveStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def archive_path(self, skill_id: str) -> Path:
        return self.root / skill_id / "archive.zip"

    def write_archive(
        self,
        skill_id: str,
        payload: bytes,
        filename: str | None = None,
    ) -> SkillArchiveMetadata:
        if not payload:
            raise ValueError("Skill 压缩包不能为空")
        self._validate_archive(skill_id, payload)
        target_dir = self.root / skill_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / "archive.zip"
        temp_path = target_dir / ".archive.zip.tmp"
        temp_path.write_bytes(payload)
        temp_path.replace(target_path)
        return SkillArchiveMetadata(
            filename=Path(filename or f"{skill_id}.zip").name or f"{skill_id}.zip",
            sha256=hashlib.sha256(payload).hexdigest(),
            size=len(payload),
        )

    def read_archive(self, skill_id: str) -> bytes:
        path = self.archive_path(skill_id)
        if not path.exists():
            raise FileNotFoundError(skill_id)
        return path.read_bytes()

    def delete_archive(self, skill_id: str) -> None:
        target_dir = self.root / skill_id
        if target_dir.exists():
            shutil.rmtree(target_dir)

    def _validate_archive(self, skill_id: str, payload: bytes) -> None:
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                skill_root = _detect_skill_root(archive, skill_id)
                skill_md_path = str(skill_root / "SKILL.md") if skill_root.parts else "SKILL.md"
                skill_md = archive.read(skill_md_path).decode("utf-8", errors="replace")
        except zipfile.BadZipFile as exc:
            raise ValueError("Skill 压缩包必须是有效的 zip 文件") from exc
        declared_name = _extract_skill_name(skill_md)
        if declared_name and declared_name != skill_id:
            raise ValueError("SKILL.md 中的 name 必须与 Skill ID 一致")


def _extract_skill_name(skill_md: str) -> str | None:
    text = skill_md.lstrip("\ufeff")
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.partition(":")[2].strip().strip("'\"")
    return None


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
