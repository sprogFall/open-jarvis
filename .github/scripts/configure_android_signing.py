from __future__ import annotations

import argparse
import base64
import binascii
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping


REQUIRED_SIGNING_VARS = (
    "ANDROID_KEYSTORE_BASE64",
    "ANDROID_KEYSTORE_PASSWORD",
    "ANDROID_KEY_PASSWORD",
    "ANDROID_KEY_ALIAS",
)


class SigningConfigurationError(RuntimeError):
    """Raised when release signing inputs are missing or invalid."""


def _write_github_output(path: Path | None, key: str, value: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{key}={value}\n")


def _normalize_keystore_secret(raw_value: str) -> str:
    match = re.search(
        r"(?mi)^\s*(?:export\s+)?ANDROID_KEYSTORE_BASE64\s*[:=]\s*(.+?)\s*$",
        raw_value,
    )
    value = match.group(1) if match else raw_value.strip()
    value = value.strip().strip("'\"").strip()
    if value.startswith("data:") and "," in value:
        value = value.split(",", 1)[1]
    return re.sub(r"\s+", "", value)


def _cleanup(paths: list[Path]) -> None:
    for path in paths:
        path.unlink(missing_ok=True)


def _validate_keystore(keystore_path: Path, store_password: str) -> None:
    try:
        result = subprocess.run(
            [
                "keytool",
                "-list",
                "-keystore",
                str(keystore_path),
                "-storepass",
                store_password,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SigningConfigurationError("keytool is required to validate the Android keystore.") from exc

    if result.returncode != 0:
        raise SigningConfigurationError("Decoded keystore failed validation.")


def configure_signing(
    *,
    build_type: str,
    env: Mapping[str, str],
    project_dir: Path,
    github_output_path: Path | None = None,
) -> str:
    keystore_path = project_dir / "android" / "app" / "upload-keystore.jks"
    key_properties_path = project_dir / "android" / "key.properties"
    _cleanup([keystore_path, key_properties_path])

    if build_type != "release":
        signing_mode = "debug"
        _write_github_output(github_output_path, "signing_mode", signing_mode)
        return signing_mode

    missing = [name for name in REQUIRED_SIGNING_VARS if not env.get(name)]
    if missing:
        joined = ", ".join(missing)
        raise SigningConfigurationError(
            f"Release build requires configured signing secrets: {joined}."
        )

    try:
        decoded = base64.b64decode(
            _normalize_keystore_secret(env["ANDROID_KEYSTORE_BASE64"]),
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise SigningConfigurationError("Invalid ANDROID_KEYSTORE_BASE64.") from exc

    keystore_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        keystore_path.write_bytes(decoded)
        _validate_keystore(keystore_path, env["ANDROID_KEYSTORE_PASSWORD"])
        key_properties_path.write_text(
            "\n".join(
                [
                    f"storePassword={env['ANDROID_KEYSTORE_PASSWORD']}",
                    f"keyPassword={env['ANDROID_KEY_PASSWORD']}",
                    f"keyAlias={env['ANDROID_KEY_ALIAS']}",
                    "storeFile=upload-keystore.jks",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        _cleanup([keystore_path, key_properties_path])
        raise

    signing_mode = "release-keystore"
    _write_github_output(github_output_path, "signing_mode", signing_mode)
    return signing_mode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-type", required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)

    try:
        configure_signing(
            build_type=args.build_type,
            env=os.environ,
            project_dir=args.project_dir,
            github_output_path=args.github_output,
        )
    except SigningConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
