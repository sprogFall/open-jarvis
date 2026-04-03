# Skill 预设配置与调用改造说明

## 背景

本次改造目标是把 Skill 从“只有 zip 归档同步”扩展为“两类能力并存”：

1. **builtin skills**：系统预置、可直接分配、可直接被 AI 发现与调用
2. **archive skills**：继续沿用 zip 归档上传、同步、解压的流程

设计约束遵循仓库根目录 `设计文档.md`：

- 保持三端闭环优先，不引入复杂插件市场
- 只在协议、状态机、技能接口上留清晰边界
- 继续支持审批、恢复、日志、离线待处理恢复

## 改造结果

### 1. 引入统一 Skill Catalog

新增 `skill_catalog.py`，作为 Gateway 与 Client 共用的内建能力清单。

当前预置 4 个 builtin skills：

- `builtin-shell`
  - `shell.exec`
- `builtin-docker`
  - `docker.list_containers`
  - `docker.restart`
- `builtin-process`
  - `process.inspect_load`
  - `process.list_processes`
- `builtin-filesystem`
  - `filesystem.read_file`
  - `filesystem.search_suffix`

每个 action 都有：

- action 名称
- 参数 schema
- 描述
- 是否需要审批
- 审批原因

### 2. Gateway 自动注册 builtin skills

Gateway 启动时会自动把 builtin skills 注册进 `skills` 目录表。

这样 Dashboard 进入 Skills 页面后就能直接看到这些预设技能，不需要额外上传 zip。

同时：

- builtin skill 的 `source` 标记为 `builtin`
- archive skill 的 `source` 标记为 `archive`
- builtin skill 默认 `archive_ready = true`
- builtin skill 会额外暴露 `action_names`

### 3. 设备 Skill 同步协议增强

`DEVICE_SKILLS_SYNC` 现在统一承载两类 skill：

- builtin：只同步元信息与 action 列表，不下发 zip 下载地址
- archive：继续同步归档校验信息与 `download_path`

Client 收到后会做两件事：

1. 更新“当前启用的 builtin action 白名单”
2. 仅对 `source=archive` 的 skill 执行 zip 下载与解压

### 4. AI 只能看到当前启用的 builtin actions

本次改造把 planner 从“硬编码 action 清单”改为“读取当前 registry 中已启用 action”。

效果：

- 某设备如果只分配了 `builtin-docker`
  - AI prompt 里只会出现 docker 相关 actions
- 没分配 `builtin-shell`
  - AI 不会看到 `shell.exec`
  - runtime 也会拒绝执行 `shell.exec`

这保证了：

- **配置层**：设备到底有什么能力，由 Gateway 分配决定
- **规划层**：AI 只能规划到已启用能力
- **执行层**：即使 AI 越权返回，也会在 runtime 被拒绝

### 5. Dashboard 展示逻辑更新

Dashboard 现在区分 builtin 与 archive：

- builtin skill：显示“内建 Skill”和可用 action 列表
- archive skill：显示 zip 状态、文件名、校验值

设备分配弹层中：

- builtin 可直接分配
- archive 仍需先上传 zip 才能分配

## 关键文件

### 核心实现

- `skill_catalog.py`
- `gateway/main.py`
- `gateway/store.py`
- `gateway/dashboard_api.py`
- `client/service.py`
- `client/runtime.py`
- `client/planner.py`
- `client/skill_runtime.py`

### 前端与文档

- `dashboard/src/types.ts`
- `dashboard/src/app/model.ts`
- `dashboard/src/app/useDashboardController.ts`
- `dashboard/src/features/skills/SkillsTab.tsx`
- `dashboard/src/features/skills/SkillEditorSheet.tsx`
- `dashboard/src/features/devices/AssignmentSheet.tsx`
- `README.md`
- `dashboard/README.md`
- `dashboard/DEPLOYMENT.md`

### 测试

- `gateway/tests/test_builtin_skill_catalog.py`
- `gateway/tests/test_gateway_flow.py`
- `gateway/tests/test_gateway_regressions.py`
- `client/tests/test_builtin_skill_registry.py`
- `client/tests/test_skill_runtime_builtin.py`

## 验证结果

本次改造完成后已验证：

```bash
pytest client/tests -q
pytest gateway/tests -q
cd dashboard && npm run build
```

均通过。

## 当前边界

本次只实现“预设 skill 的优雅配置与调用”，没有扩展到：

- 插件市场
- 多租户技能仓库
- 分布式调度
- 任意第三方远程 tool provider

也就是说，当前方案仍然保持初始化阶段所要求的“克制扩展性”。

## 后续建议

如果后续继续演进，可沿当前边界前进：

1. 给 archive skill 增加可选 manifest 字段，描述它实际暴露的 action
2. 为 builtin/archive skill 增加更细粒度的审批策略
3. 在 Gateway 侧增加“设备已启用 action 总览”接口，便于运维排查
4. 在 App 侧展示任务执行所依赖的 skill 来源（builtin / archive）
