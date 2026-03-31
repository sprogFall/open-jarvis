from __future__ import annotations

import base64
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / ".github" / "scripts" / "configure_android_signing.py"


def load_signing_module():
    spec = importlib.util.spec_from_file_location("configure_android_signing", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.pop("configure_android_signing", None)
    spec.loader.exec_module(module)
    return module


def create_android_layout(project_dir: Path) -> tuple[Path, Path]:
    keystore_path = project_dir / "android" / "app" / "upload-keystore.jks"
    key_properties_path = project_dir / "android" / "key.properties"
    keystore_path.parent.mkdir(parents=True, exist_ok=True)
    return keystore_path, key_properties_path


def generate_keystore(keystore_path: Path, *, store_password: str, key_alias: str) -> bytes:
    subprocess.run(
        [
            "keytool",
            "-genkeypair",
            "-storetype",
            "JKS",
            "-keystore",
            str(keystore_path),
            "-storepass",
            store_password,
            "-keypass",
            store_password,
            "-alias",
            key_alias,
            "-dname",
            "CN=OpenJarvis CI, OU=Dev, O=OpenJarvis, L=Test, S=Test, C=US",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "3650",
            "-noprompt",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return keystore_path.read_bytes()


def test_debug_build_skips_release_signing_configuration(tmp_path):
    module = load_signing_module()
    keystore_path, key_properties_path = create_android_layout(tmp_path)
    github_output = tmp_path / "github-output.txt"

    signing_mode = module.configure_signing(
        build_type="debug",
        env={},
        project_dir=tmp_path,
        github_output_path=github_output,
    )

    assert signing_mode == "debug"
    assert github_output.read_text() == "signing_mode=debug\n"
    assert not keystore_path.exists()
    assert not key_properties_path.exists()


def test_release_build_without_secrets_fails_fast(tmp_path):
    module = load_signing_module()
    keystore_path, key_properties_path = create_android_layout(tmp_path)

    with pytest.raises(module.SigningConfigurationError, match="requires configured signing secrets"):
        module.configure_signing(
            build_type="release",
            env={},
            project_dir=tmp_path,
        )

    assert not keystore_path.exists()
    assert not key_properties_path.exists()


def test_release_build_with_invalid_base64_fails_fast(tmp_path):
    module = load_signing_module()
    keystore_path, key_properties_path = create_android_layout(tmp_path)

    with pytest.raises(module.SigningConfigurationError, match="Invalid ANDROID_KEYSTORE_BASE64"):
        module.configure_signing(
            build_type="release",
            env={
                "ANDROID_KEYSTORE_BASE64": "%%%not-base64%%%",
                "ANDROID_KEYSTORE_PASSWORD": "store-pass",
                "ANDROID_KEY_PASSWORD": "store-pass",
                "ANDROID_KEY_ALIAS": "upload",
            },
            project_dir=tmp_path,
        )

    assert not keystore_path.exists()
    assert not key_properties_path.exists()


def test_release_build_with_invalid_keystore_fails_fast(tmp_path):
    module = load_signing_module()
    keystore_path, key_properties_path = create_android_layout(tmp_path)

    with pytest.raises(module.SigningConfigurationError, match="Decoded keystore failed validation"):
        module.configure_signing(
            build_type="release",
            env={
                "ANDROID_KEYSTORE_BASE64": base64.b64encode(b"not-a-keystore").decode(),
                "ANDROID_KEYSTORE_PASSWORD": "store-pass",
                "ANDROID_KEY_PASSWORD": "store-pass",
                "ANDROID_KEY_ALIAS": "upload",
            },
            project_dir=tmp_path,
        )

    assert not keystore_path.exists()
    assert not key_properties_path.exists()


def test_release_build_with_valid_keystore_writes_key_properties(tmp_path):
    module = load_signing_module()
    project_keystore_path, key_properties_path = create_android_layout(tmp_path)
    generated_keystore = tmp_path / "fixture-upload.jks"
    store_password = "store-pass"
    key_alias = "upload"
    keystore_bytes = generate_keystore(
        generated_keystore,
        store_password=store_password,
        key_alias=key_alias,
    )
    github_output = tmp_path / "github-output.txt"

    signing_mode = module.configure_signing(
        build_type="release",
        env={
            "ANDROID_KEYSTORE_BASE64": base64.b64encode(keystore_bytes).decode(),
            "ANDROID_KEYSTORE_PASSWORD": store_password,
            "ANDROID_KEY_PASSWORD": store_password,
            "ANDROID_KEY_ALIAS": key_alias,
        },
        project_dir=tmp_path,
        github_output_path=github_output,
    )

    assert signing_mode == "release-keystore"
    assert project_keystore_path.read_bytes() == keystore_bytes
    assert key_properties_path.read_text() == (
        "storePassword=store-pass\n"
        "keyPassword=store-pass\n"
        "keyAlias=upload\n"
        "storeFile=app/upload-keystore.jks\n"
    )
    assert github_output.read_text() == "signing_mode=release-keystore\n"
