"""工具规格基类。

对应架构设计第 6 节：名称、说明、JSON Schema、权限等级、超时、是否幂等、结果大小上限。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class PermissionLevel(StrEnum):
    read = "read"
    write = "write"
    network = "network"
    code_exec = "code_exec"



class ToolSpec(BaseModel):
    """工具规格定义。

    每个注册到系统的工具都必须提供一份 ToolSpec，作为工具的"身份证"。
    它同时服务于三个角色：
    1. LLM — 通过 description + parameters_schema 理解何时以及如何调用工具；
    2. 运行引擎 — 通过 timeout_seconds + max_result_size 控制执行边界；
    3. 安全层 — 通过 permission_level + idempotent 决定是否允许执行和重试。
    """

    name: str
    """工具的唯一标识名称。

    - 全局唯一，注册表通过此字段索引工具
    - 建议使用 snake_case，如 "web_search"、"create_file"
    - Agent 的 function call 中以此名称匹配工具
    """

    description: str
    """工具的功能描述，会注入到 LLM 的 system prompt 中。

    模型根据此描述判断"当前任务是否应该使用这个工具"。描述越精准，
    模型在正确时机调用工具的概率越高。

    建议写法：
    - 先说清楚工具做什么（核心功能一句话）
    - 再列出适用/不适用场景（帮助模型做排除）
    - 不要写参数细节（参数由 parameters_schema 自动描述）
    """

    parameters_schema: dict[str, Any]
    """工具输入参数的 JSON Schema 定义。

    LLM 根据此 Schema 生成符合要求的 JSON 参数调用工具。
    通常直接从 Pydantic model 的 model_json_schema() 方法生成，
    避免手动维护两套参数定义。

    示例结构：
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"]
        }
    """

    permission_level: PermissionLevel = PermissionLevel.read
    """工具所需的最低权限等级。

    默认值为 read（最安全）。工具作者应根据实际操作类型显式设置：
    - 纯查询 → read
    - 有写入 → write
    - 调外网 → network
    - 跑代码 → code_exec

    运行时会校验：调用者的授权等级 >= 工具的 permission_level。
    """

    timeout_seconds: int = 30
    """工具单次调用的最大执行时间（秒）。

    - 超时后运行引擎会中断执行并向 Agent 返回超时错误
    - 防止某个工具卡死导致整个 Agent 流程无限等待
    - 默认 30 秒适合大多数查询类工具；长时间任务可适当调大
    """

    idempotent: bool = True
    """工具是否满足幂等性——重复调用是否产生相同结果且无额外副作用。

    - True：可安全重试。失败后 Agent 自动重试，不会造成重复操作。
      适用于：搜索、读取、状态查询。
    - False：每次调用可能产生新副作用。重试前需要确认或跳过自动重试。
      适用于：发送消息、创建订单、扣款。

    默认 True 是保守策略，工具作者应如实标注非幂等工具。
    """

    max_result_size: int = 16_384
    """工具返回结果的最大字节数（约等于字符数）。

    - 当结果超过此限制时，引擎会截断返回内容
    - 目的有两个：
      1. 保护 LLM context window 不被单个工具结果撑满
      2. 控制单次工具调用的 token 成本和延迟
    - 默认 16KB 是大多数场景的合理上限
    """

    executor: Any | None = None
    """工具的实际可调用对象（LangChain @tool 函数或 BaseTool 实例）。

    None 表示仅注册元数据，暂不提供可执行体。
    executor 中注册时传入实际函数，executor 节点通过此字段直接获取。
    """

__all__ = ["PermissionLevel", "ToolSpec"]
