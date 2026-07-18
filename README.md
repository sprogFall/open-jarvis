# Open Jarvis

基于 LangChain + LangGraph 的可恢复、多任务 Agent 编排系统。

> 详细架构见 [架构设计.md](./架构设计.md)、流程见 [流程设计.md](./流程设计.md)。

## 技术栈

- **语言**：Python 3.12+
- **依赖管理**：[uv](https://docs.astral.sh/uv/)
- **Web 框架**：FastAPI + Uvicorn + sse-starlette
- **Agent**：LangChain + LangGraph（含 PostgreSQL Checkpointer）
- **数据建模**：Pydantic v2 + pydantic-settings
- **持久化**：PostgreSQL（asyncpg + SQLAlchemy 2.x + Alembic）、Redis
- **可观测性**：OpenTelemetry + structlog
- **前端**：预留 `web/` 目录，后续按需初始化

## 项目结构

```text
open-jarvis/
├─ app/
│  ├─ api/                 # FastAPI 路由、SSE、鉴权
│  │  ├─ router.py
│  │  └─ v1/               # /api/v1 路由（runs、health）
│  ├─ graph/
│  │  ├─ builder.py        # StateGraph 构建与条件路由
│  │  ├─ state.py          # RunState 与 reducers
│  │  ├─ nodes/            # planner/scheduler/executor/...
│  │  └─ prompts/          # 版本化 Prompt 模板
│  ├─ domain/              # Plan、Task、Review、Experience 等领域模型
│  ├─ tools/               # 工具注册、权限、执行与适配器
│  ├─ models/              # LLM 配置与模型路由（fast/standard/reasoning）
│  ├─ repositories/        # PostgreSQL / Redis 数据访问
│  ├─ services/            # run、event、artifact、experience 服务
│  ├─ worker/              # 队列消费、恢复、心跳
│  └─ observability/       # 日志、指标、Trace
├─ migrations/             # Alembic 迁移
├─ tests/
│  ├─ unit/                # 节点、路由、DAG、reducer
│  ├─ integration/         # PostgreSQL、Redis、工具适配
│  └─ scenarios/           # 端到端固定场景与质量回归
├─ web/                    # 前端目录（待初始化）
├─ pyproject.toml          # uv 依赖管理
├─ alembic.ini
└─ .env.example            # 环境变量模板
```

## 快速开始

### 1. 安装依赖

需先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)：

```bash
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 按需修改 .env 中的数据库、Redis、LLM 密钥
```

### 3. 启动 API

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs` 查看 API 文档。

### 4. 启动 Worker（生产环境独立进程）

```bash
uv run python -m app.worker.consumer
```

### 5. 数据库迁移

```bash
uv run alembic upgrade head
```

### 6. 运行测试

```bash
uv run pytest
```

### 7. 代码检查

```bash
uv run ruff check .
uv run ruff format .
uv run mypy app
```

## 前端

前端工程位于 `web/` 目录，后续可使用任意现代框架初始化（React/Vue 等）。后端通过 `/api/v1` 提供服务，前端可通过 SSE 订阅运行实时进度。

## 开发约定

- 图负责流程，状态负责事实：节点只读取 `RunState` 并返回增量更新。
- 并行 Executor 不修改共享 `tasks`，只追加不可变 `TaskResult`。
- 大对象不进入图状态，使用引用。
- 密钥只从环境变量注入，不进入 Prompt、Checkpoint、日志和 SSE。
