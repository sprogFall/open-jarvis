from __future__ import annotations

from pathlib import Path


class FileSystemSkill:
    def __init__(self, allowed_roots: list[Path]) -> None:
        self.allowed_roots = [Path(root).expanduser().resolve() for root in allowed_roots]

    def _resolve(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser().resolve()
        for root in self.allowed_roots:
            try:
                path.relative_to(root)
                return path
            except ValueError:
                continue
        raise PermissionError(f"Path is outside allowed roots: {raw_path}")

    def read_file(self, raw_path: str) -> str:
        return self._resolve(raw_path).read_text(encoding="utf-8")

    def search_suffix(self, suffix: str) -> str:
        matches: list[str] = []
        for root in self.allowed_roots:
            for path in root.rglob(f"*{suffix}"):
                if path.is_file():
                    matches.append(str(path))
        return "\n".join(sorted(matches)) if matches else "No files matched"
