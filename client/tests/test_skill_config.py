from pathlib import Path

from client.config import ClientConfig
from client.service import build_default_registry, merge_skill_config


def test_merge_skill_config_filesystem_assignment_priority():
    """测试filesystem skill配置合并：assignment级配置优先"""
    config = ClientConfig(allowed_roots=[Path("/default")])

    merged = merge_skill_config(
        skill_id="builtin-filesystem",
        skill_config={"allowed_roots": "/skill/path"},
        assignment_config={"allowed_roots": "/assignment/path"},
        client_config=config,
    )
    assert merged["allowed_roots"] == [Path("/assignment/path")]


def test_merge_skill_config_filesystem_skill_fallback():
    """测试filesystem skill配置合并：回退到skill级配置"""
    config = ClientConfig(allowed_roots=[Path("/default")])

    merged = merge_skill_config(
        skill_id="builtin-filesystem",
        skill_config={"allowed_roots": "/skill/path"},
        assignment_config={},
        client_config=config,
    )
    assert merged["allowed_roots"] == [Path("/skill/path")]


def test_merge_skill_config_filesystem_env_fallback():
    """测试filesystem skill配置合并：回退到环境变量"""
    config = ClientConfig(allowed_roots=[Path("/default")])

    merged = merge_skill_config(
        skill_id="builtin-filesystem",
        skill_config={},
        assignment_config={},
        client_config=config,
    )
    assert merged["allowed_roots"] == [Path("/default")]


def test_merge_skill_config_filesystem_comma_separated():
    """测试filesystem skill配置合并：逗号分隔字符串"""
    config = ClientConfig(allowed_roots=[Path("/default")])

    merged = merge_skill_config(
        skill_id="builtin-filesystem",
        skill_config={},
        assignment_config={"allowed_roots": "/path1,/path2, /path3 "},
        client_config=config,
    )
    assert merged["allowed_roots"] == [Path("/path1"), Path("/path2"), Path("/path3")]


def test_merge_skill_config_iot_assignment_priority():
    """测试iot skill配置合并：assignment级配置优先"""
    config = ClientConfig(iot_base_url="http://default", iot_token="default_token")

    merged = merge_skill_config(
        skill_id="builtin-iot",
        skill_config={"base_url": "http://skill", "token": "skill_token"},
        assignment_config={"base_url": "http://assignment", "token": "assignment_token"},
        client_config=config,
    )
    assert merged["base_url"] == "http://assignment"
    assert merged["token"] == "assignment_token"


def test_merge_skill_config_iot_partial_override():
    """测试iot skill配置合并：部分覆盖"""
    config = ClientConfig(iot_base_url="http://default", iot_token="default_token")

    merged = merge_skill_config(
        skill_id="builtin-iot",
        skill_config={"base_url": "http://skill"},
        assignment_config={"token": "assignment_token"},
        client_config=config,
    )
    assert merged["base_url"] == "http://skill"
    assert merged["token"] == "assignment_token"


def test_merge_skill_config_iot_env_fallback():
    """测试iot skill配置合并：回退到环境变量"""
    config = ClientConfig(iot_base_url="http://default", iot_token="default_token")

    merged = merge_skill_config(
        skill_id="builtin-iot",
        skill_config={},
        assignment_config={},
        client_config=config,
    )
    assert merged["base_url"] == "http://default"
    assert merged["token"] == "default_token"


def test_merge_skill_config_unknown_skill():
    """测试未知skill返回空配置"""
    config = ClientConfig()

    merged = merge_skill_config(
        skill_id="unknown-skill",
        skill_config={"foo": "bar"},
        assignment_config={"baz": "qux"},
        client_config=config,
    )
    assert merged == {}


def test_build_registry_with_device_skills():
    """测试registry使用device_skills配置"""
    config = ClientConfig(allowed_roots=[Path("/default")])
    device_skills = [
        {
            "skill_id": "builtin-filesystem",
            "source": "builtin",
            "config": {"allowed_roots": "/custom/path"},
            "skill_config": {},
        }
    ]

    registry = build_default_registry(config, device_skills=device_skills)
    assert registry is not None


def test_build_registry_without_device_skills():
    """测试registry不传device_skills时保持向后兼容"""
    config = ClientConfig(allowed_roots=[Path("/default")])

    registry = build_default_registry(config, enable_builtin_by_default=True)
    assert registry is not None


def test_build_registry_with_empty_device_skills():
    """测试registry传入空device_skills列表"""
    config = ClientConfig(allowed_roots=[Path("/default")])

    registry = build_default_registry(config, device_skills=[], enable_builtin_by_default=False)
    assert registry is not None
