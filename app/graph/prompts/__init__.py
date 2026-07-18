"""版本化 Prompt 模板与节点专用输出 schema。

每个节点一个模块，导出：
- XXX_PROMPT：ChatPromptTemplate
- XXXDraft（如需结构化输出）：LLM 直接填充的 Pydantic 模型

版本策略：模板变更时在模块内新增 v2 常量并切换引用，旧版本保留以便回滚。
"""

__all__: list[str] = []