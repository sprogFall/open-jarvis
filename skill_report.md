# Skill 使用与配置模式现状评估

## 1. 说明

本报告以根目录 `设计文档.md` 为设计基准，并结合当前仓库实现整理 Skill 的现状与改进方向。

当前实现已经形成一条可工作的闭环，但它更接近“Skill 目录管理 + 分配同步 + archive 下发”，还没有完全走到“所有 Skill 都能被统一配置、统一发现、统一调用”的状态。

## 2. 当前 Skill 模式是什么样

### 2.1 Skill 已经分成两类

- `builtin skill`
  - 定义在 `skill_catalog.py`
  - Gateway 启动时自动注册到 `skills` 表
  - 具备明确的 `action_names`
  - 可直接分配给设备
  - 会直接进入 Client 侧 action registry，AI 可见、可规划、可执行

- `archive skill`
  - 通过 Dashboard 创建目录项，再上传 zip 归档
  - zip 里必须包含 `SKILL.md`
  - 分配给设备后，Gateway 通过 `DEVICE_SKILLS_SYNC` 下发元信息和下载地址
  - Client 只负责下载、校验、解压到本地 workspace
  - 当前不会进入统一 action registry，AI 默认看不到也不能直接调用

### 2.2 当前 Skill 的“使用链路”

- Skill 目录管理
  - Dashboard 调 `/dashboard/api/skills` 创建、编辑、删除 Skill
  - archive skill 再单独调 `/dashboard/api/skills/{skill_id}/archive` 上传 zip

- 设备分配
  - Dashboard 调 `/dashboard/api/devices/{device_id}/skills`
  - Gateway 把设备分配结果写到 `device_skills`
  - 若设备在线，会立即推送 `DEVICE_SKILLS_SYNC`

- Client 侧处理
  - builtin skill：只同步元信息与 action 列表，用来启用/禁用 action
  - archive skill：下载 zip，校验 sha256，解压到 `OMNI_AGENT_SKILLS_WORKSPACE/<skill_id>/`
  - 解压后会写入 `.open-jarvis-skill.json`，保存 `skill_config` 和 `assignment_config`

- AI 调用
  - `LLMPlanner` 只读取当前 registry 中已启用的 action
  - registry 当前只真正接入 builtin action
  - 所以“分配 archive skill”目前主要是下发资源，不是直接扩充 AI 工具能力

### 2.3 当前 Skill 的“配置层”其实有三层

- Skill 全局配置
  - 存在 `skills.config_json`
  - 在 Dashboard 的 Skill 编辑弹层里以“配置 JSON”维护

- 设备分配配置
  - 存在 `device_skills.config_json`
  - 在设备分配弹层里以“分配配置 JSON”维护

- Client 本地运行环境配置
  - 主要来自环境变量
  - 例如 `OMNI_AGENT_ALLOWED_ROOTS`、`OMNI_AGENT_IOT_BASE_URL`、`OMNI_AGENT_IOT_TOKEN`

### 2.4 当前配置真正被谁消费

- builtin skill 的真实运行时配置，目前主要还是 Client 环境变量
  - 例如文件系统技能依赖 `OMNI_AGENT_ALLOWED_ROOTS`
  - IoT 技能依赖 `OMNI_AGENT_IOT_BASE_URL` 和 `OMNI_AGENT_IOT_TOKEN`

- Skill 全局配置和设备分配配置，目前会被同步、会落盘，但很少进入真实执行逻辑
  - 它们更多还是“被保存下来”
  - 还没有形成稳定的“配置驱动执行”模型

### 2.5 三端现状并不对称

- Gateway
  - 已经承担 Skill 目录、分配、归档存储、设备同步

- Dashboard
  - 已经承担 Skill 创建、zip 上传、分配、快速部署包选 Skill

- App
  - 当前基本没有 Skill 视角的展示和配置能力
  - 仍然以任务、审批、日志为主
  - 用户在 App 中很难知道某个任务依赖了哪些 Skill、来自 builtin 还是 archive、为什么某个动作能/不能执行

## 3. 当前模式的优点

- 分层清楚
  - Gateway 管目录和同步
  - Client 管执行和本地落地
  - Dashboard 管运营入口

- builtin skill 已经形成“可控能力白名单”
  - 分配决定能力
  - prompt 只暴露已启用 action
  - runtime 还能拒绝越权 action

- archive skill 已经具备安全边界
  - 必须显式上传
  - 必须分配到设备
  - 必须由设备签名后才能下载

- 扩展性仍然克制
  - 还没有引入插件市场、多租户、远程 provider 编排
  - 这一点符合当前阶段目标

## 4. 当前模式的主要问题

### 4.1 上传流程是“两步式”，不够顺手

- 先创建 Skill
- 再上传 archive
- 创建失败和上传失败是两个事务
- 前端已经做了失败回滚，但用户心智仍然是割裂的

### 4.2 Skill 契约不统一

- builtin skill 有结构化 action 定义
- archive skill 只有 zip 和 `SKILL.md`
- `SKILL.md` 当前更多只用于“是否存在”和“name 是否匹配”
- archive skill 没有被解析成统一的 action/config/审批契约

### 4.3 配置方式过于原始

- Dashboard 当前主要靠 JSON 文本框
- 没有 schema
- 没有字段级校验
- 没有默认值说明
- 没有“这个配置最终怎么生效”的可视化

### 4.4 “已配置”不等于“可调用”

- archive skill 可以上传、分配、同步、解压
- 但不会自动进入 action registry
- 这会让“Skill 已经在设备上”与“AI 现在能调用这个 Skill”之间存在明显语义断层

### 4.5 配置层级不清晰

- Skill 全局 config
- device assignment config
- Client env config
- 三者都存在，但优先级和职责没有被正式定义
- 用户很难判断某个行为到底受哪一层控制

### 4.6 缺少版本与回滚语义

- archive 目前以 `skill_id -> 当前 zip` 为主
- 没有显式版本号、发布记录、设备绑定版本
- 更新 zip 会直接覆盖当前版本
- 对线上排障和灰度不够友好

### 4.7 调用侧缺少“能力可见性”

- Dashboard 可以看到 Skill 目录和设备分配
- 但没有“这个设备当前最终启用了哪些 action、哪些需要审批、哪些来自 builtin/archive”的统一视图
- App 侧基本没有 Skill 可见性

## 5. 可以优先改进的方向

以下方向都尽量保持克制，不引入插件市场、分布式调度或复杂远程执行框架。

### 5.1 统一成一个 Skill Manifest 契约

建议新增统一 manifest 概念，builtin 与 archive 都按同一套结构表达。

manifest 至少包含：

- `skill_id`
- `name`
- `version`
- `description`
- `source`
- `actions`
- `default_config`
- `assignment_config_schema`
- `skill_config_schema`
- `required_mounts`
- `approval_policy`

推荐做法：

- builtin skill 继续保留在 `skill_catalog.py`
- 但内部数据结构升级成统一 manifest
- archive skill 上传时，从 zip 中解析 manifest
- `SKILL.md` 保留给说明文档
- 再单独增加机器可读的 `skill.json` 或 `skill.yaml`

价值：

- 上传、配置、分配、调用都围绕同一份契约
- builtin 和 archive 的用户体验可以趋同
- 后续 App / Dashboard 展示也有统一数据来源

### 5.2 提供“一步导入”而不是“先建后传”

建议增加一个原子化导入入口，例如：

- `POST /dashboard/api/skills/import`

导入流程：

- 上传 zip
- 解析 manifest
- 自动识别 `skill_id/name/version/description`
- 校验 archive
- 创建或更新 Skill
- 返回完整 Skill DTO

Dashboard 上对应改成：

- “上传 Skill 包”
- 自动回填基础信息
- 允许用户只改少量字段后确认

这样比现在的“两步式创建 + 上传”更符合用户直觉。

### 5.3 把 JSON 文本框升级成“schema 驱动配置”

建议区分两类 schema：

- `skill_config_schema`
  - 维护 Skill 默认配置
  - 例如默认 workspace、默认模式、默认审批策略

- `assignment_config_schema`
  - 维护设备分配覆盖项
  - 例如该设备专用目录、该设备专用参数

Dashboard 可以根据 schema 自动渲染表单，而不是只给一个 JSON 输入框。

最小可行能力：

- 字段名称
- 类型
- 必填
- 默认值
- 枚举
- 文案说明
- 字段级校验错误提示

再补一个“最终生效配置预览”：

- effective config = skill default config + assignment override + device env derived config

这能明显降低“配了但不知道是否生效”的问题。

### 5.4 给设备提供统一的“可调用能力视图”

建议 Gateway 增加一个聚合视图，直接输出某设备最终可用的能力清单。

例如：

- `GET /dashboard/api/devices/{device_id}/capabilities`

返回内容建议包含：

- action 名
- 来源 skill
- source 是 builtin 还是 archive
- 参数 schema
- 是否需要审批
- 审批原因
- 是否启用
- 最终生效配置摘要

价值：

- Dashboard 可直接显示“这个设备到底能做什么”
- App 也能复用同一 DTO
- 任务排障时更清晰

### 5.5 让 archive skill 也进入统一调用模型

这是最关键的能力补齐点。

当前 archive skill 只完成了“分发”，还没有完成“调用”。

建议采用一个克制的最小方案：

- archive manifest 中声明 `actions`
- 每个 action 指向固定入口
  - Python module entry
  - 或受控命令入口
- Client 增加一个 `ArchiveSkillAdapter`
- adapter 按 manifest 装载 action，并注册进同一个 `ActionRegistry`

这样可以保持：

- builtin skill 和 archive skill 在 planner 看来都是 action catalog
- 审批、日志、恢复仍沿用现有任务闭环
- 不需要先做复杂插件市场

如果短期不想直接执行 archive 代码，至少也应先做到：

- archive manifest 能声明 action
- Gateway / Dashboard / App 能展示这些 action
- planner 可明确知道“这个 skill 只是资源包，还是可执行工具包”

### 5.6 明确配置优先级和职责

建议正式约定：

- 环境配置
  - 负责设备级基础能力和密钥
  - 例如根目录、IoT 凭据、运行目录

- skill default config
  - 负责 Skill 的默认行为

- assignment config
  - 负责某台设备上的覆盖项

同时在文档和接口里固定一个优先级顺序，例如：

- env base
- skill default
- assignment override

并在 Client 元数据文件里直接写入 `effective_config`，避免每次排障都去人工合并三层。

### 5.7 引入版本、发布与回滚语义

建议 archive skill 至少增加：

- `version`
- `archive_sha256`
- `published_at`
- `release_notes`

设备分配关系上建议记录：

- 当前绑定的 version
- 是否自动跟随最新版本

这样可以支持：

- 灰度发布
- 回滚
- 问题归因

这比现在直接覆盖 zip 更适合真实环境。

### 5.8 补一个本地打包/校验工具

建议复用现有 `jarvisctl` 思路，增加：

- `jarvisctl skill init`
- `jarvisctl skill pack`
- `jarvisctl skill validate`
- `jarvisctl skill publish`

最小价值：

- 本地校验 manifest
- 校验 `SKILL.md`
- 校验 action/schema 格式
- 直接产出 zip
- 可选直传 Gateway

这样会显著降低“做 skill 包”的门槛，也比手工 zip 更稳定。

### 5.9 App 侧补最小 Skill 可见性

App 不一定现在就要做完整 Skill 管理，但建议至少补以下只读能力：

- 当前会话绑定设备的 Skill 列表
- 当前任务用到的 action 来源
- 当前动作是否需要审批
- 当任务失败时，提示“设备未启用对应 Skill”还是“Skill 已启用但执行失败”

这会让审批和恢复流程更可理解。

## 6. 推荐的落地顺序

### 第一阶段：先把“上传与配置”做顺

- 统一 manifest
- 增加一键导入接口
- Dashboard 改成导入即建档
- 给 Skill / Assignment 配置补 schema 与表单渲染

这一阶段完成后，上传和配置会明显顺手，但不会破坏现有链路。

### 第二阶段：把“可见性”补全

- 增加 device capabilities 聚合接口
- Dashboard 显示最终 action 视图
- App 增加最小只读展示
- 明确 config 优先级，并输出 effective config

这一阶段完成后，“配了什么、能做什么、为什么不能做”会清晰很多。

### 第三阶段：补 archive skill 的统一调用

- archive manifest 声明 action
- Client 引入 archive action adapter
- archive action 接入审批、日志、恢复闭环

这一阶段完成后，Skill 才真正接近设计文档里“所有能力都以 Skill 形式存在”的目标。

## 7. 我认为最值得先做的三件事

- 第一，统一 manifest
  - 这是后续上传、配置、展示、调用的共同基座

- 第二，改成一步导入 + schema 配置
  - 这是最直接改善“上传、配置麻烦”的地方

- 第三，补设备级 capability 视图
  - 这是最直接改善“调用时不清晰”的地方

如果只能再进一步做一件核心能力，我会选：

- 让 archive skill 也能声明并接入 action catalog

因为这一步会真正打通“Skill 已上传”到“AI 可调用”的最后一段断层。

## 8. 不建议现在做的事

- 不建议引入插件市场
- 不建议做多租户 Skill 仓库
- 不建议做远程 Skill Provider 编排
- 不建议为了未来能力预建复杂调度层

这些都不符合当前阶段“三端交互正常、功能闭环优先、扩展性保持克制”的原则。

## 9. 总结

当前 Skill 模式已经具备：

- 目录管理
- 归档上传
- 设备分配
- Client 同步
- builtin action 白名单执行

但它仍然存在一个核心不对称：

- builtin skill 是“可调用能力”
- archive skill 目前更像“可分发资源”

因此，最合理的演进方向不是继续堆更多入口，而是把 Skill 统一成一份机器可读契约，再把上传、配置、展示、调用都围绕这份契约收敛。这样既符合 `设计文档.md` 的 Skill 化方向，也能保持当前阶段要求的克制扩展。
