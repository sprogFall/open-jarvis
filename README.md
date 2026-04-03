# Omni-Agent

初始化实现包含四个模块：

- `gateway`: FastAPI 网关，负责任务状态、审批持久化、JWT 与设备鉴权、WebSocket 路由。
- `dashboard`: 独立静态前端项目，负责设备/Skill/任务管理，可通过 `npm run build` 输出 `dist/` 并部署到 Nginx。
- `client`: Python 执行端，基于 LangGraph 驱动规划/执行/审批中断恢复，负责技能执行、本地 checkpoint、日志脱敏。
- `app`: Flutter 控制端，负责待审批恢复、任务派发、命令预览与实时日志工作台。

---

## 快速开始

### 前置依赖

- Docker & Docker Compose（推荐，仓库已内置完整容器栈）
- Python 3.11+（本地调试 `gateway` / `client`）
- Node.js 20+（本地调试 `dashboard`）
- Flutter 3.x（移动端开发）

### 本地开发（SQLite）

不配置 `DATABASE_URL` 时自动使用 SQLite，无需 PostgreSQL：

```bash
pip install -r requirements.txt -r gateway/requirements.txt
pytest -q
uvicorn gateway.main:app --reload
```

如需启动 Dashboard 前端：

```bash
cd dashboard
npm install
npm run dev
```

### 容器部署（开箱即用）

拉取仓库后，`docker-compose.yml` 会同时启动：

- `postgres`：内置 PostgreSQL
- `gateway`：API、WebSocket、审批状态机、本机执行端
- `client`：CLI 执行端
- `dashboard`：内置 Nginx，提供 `/jarvis/dashboard/` 静态站点并反代 `/jarvis/api`

```bash
# 1. 准备环境变量
cp .env.example .env
# 至少修改 JWT、管理员密码、设备密钥、数据库密码
# 国内网络可把 CLIENT_DOCKERFILE 改成 client/Dockerfile.cn

# 2. 构建并启动全部容器
docker compose up --build -d

# 3. 查看状态
docker compose ps
docker compose logs -f gateway client dashboard
```

启动后默认访问地址：

- Dashboard：`http://localhost:8080/jarvis/dashboard/`
- Gateway 健康检查：`http://localhost:8000/health`
- Flutter App 网关地址：`http://<宿主机IP>:8080/jarvis/api`

> Flutter App 仍需单独运行或打包安装；它不是常驻服务容器的一部分。

---

## 环境变量

### Compose / Gateway 侧

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `POSTGRES_DB` | `jarvis` | Compose 内置 PostgreSQL 数据库名 |
| `POSTGRES_USER` | `jarvis` | Compose 内置 PostgreSQL 用户名 |
| `POSTGRES_PASSWORD` | `jarvis` | Compose 内置 PostgreSQL 密码，生产环境务必修改 |
| `DATABASE_URL` | 空 | 留空时自动回退到 Compose 内置 PostgreSQL；也可显式改为外部 PostgreSQL 连接串 |
| `GATEWAY_PORT` | `8000` | Gateway 宿主机映射端口 |
| `DASHBOARD_PORT` | `8080` | Dashboard 宿主机映射端口 |
| `VITE_GATEWAY_BASE_URL` | `/jarvis/api` | Dashboard 构建时写入的 API 基地址 |
| `OMNI_AGENT_JWT_SECRET` | `change-me-change-me-change-me-1234` | JWT 签名密钥，生产环境务必修改 |
| `OMNI_AGENT_ADMIN_USERNAME` | `operator` | 管理员账号，用于登录 Dashboard 和 App |
| `OMNI_AGENT_ADMIN_PASSWORD` | `passw0rd` | 管理员密码，生产环境务必修改 |
| `OMNI_AGENT_DEVICE_KEYS` | `device-alpha=device-secret` | 预注册设备，格式 `id1=key1,id2=key2` |
| `OMNI_AGENT_DASHBOARD_ORIGINS` | 空 | Dashboard 跨域白名单；同域反代部署时通常无需设置 |
| `OMNI_AGENT_GATEWAY_ALLOWED_ROOTS` | `/workspace` | Gateway 本机执行端可访问的文件根目录，使用 `:` 分隔 |
| `OMNI_AGENT_GATEWAY_LOCAL_CHECKPOINT_DB` | `/data/gateway/local-client.db` | Gateway 本机执行端 checkpoint 路径 |
| `OMNI_AGENT_GATEWAY_LOCAL_LANGGRAPH_DB` | `/data/gateway/local-langgraph.db` | Gateway 本机执行端 LangGraph 状态路径 |
| `OMNI_AGENT_SKILL_ARCHIVES_DIR` | `/data/gateway/skill-archives` | Gateway 侧 archive skill 归档目录 |
| `OMNI_AGENT_GATEWAY_IOT_BASE_URL` | 空 | Gateway 侧 IoT 平台接口地址 |
| `OMNI_AGENT_GATEWAY_IOT_TOKEN` | 空 | Gateway 侧 IoT Token |
| `OMNI_AGENT_GATEWAY_AI_PROVIDER` | 空 | Gateway 侧 AI 供应商标识 |
| `OMNI_AGENT_GATEWAY_AI_MODEL` | 空 | Gateway 侧 AI 模型名 |
| `OMNI_AGENT_GATEWAY_AI_API_KEY` | 空 | Gateway 侧 AI Key |
| `OMNI_AGENT_GATEWAY_AI_BASE_URL` | 空 | Gateway 侧自定义或 OpenAI-compatible 基地址 |

### Client 端环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OMNI_AGENT_GATEWAY_URL` | `http://gateway:8000` | Client 连接 Gateway 的内部地址 |
| `OMNI_AGENT_DEVICE_ID` | `device-alpha` | 当前设备标识 |
| `OMNI_AGENT_DEVICE_KEY` | `device-secret` | 当前设备签名密钥，需与 Gateway 侧一致 |
| `OMNI_AGENT_CHECKPOINT_DB` | `/data/client/client.db` | Client checkpoint 存储路径 |
| `OMNI_AGENT_LANGGRAPH_DB` | `/data/client/langgraph.db` | Client LangGraph workflow 状态路径 |
| `OMNI_AGENT_SKILLS_WORKSPACE` | `/data/client/skills-runtime` | archive skill 下载/解压目录 |
| `OMNI_AGENT_ALLOWED_ROOTS` | `/workspace` | 文件系统技能允许访问的根目录 |
| `OMNI_AGENT_IOT_BASE_URL` | 空 | Client 侧 IoT 平台接口地址 |
| `OMNI_AGENT_IOT_TOKEN` | 空 | Client 侧 IoT Token |
| `OMNI_AGENT_CLIENT_AI_PROVIDER` | 空 | Client 侧 AI 供应商标识 |
| `OMNI_AGENT_CLIENT_AI_MODEL` | 空 | Client 侧 AI 模型名 |
| `OMNI_AGENT_CLIENT_AI_API_KEY` | 空 | Client 侧 AI Key |
| `OMNI_AGENT_CLIENT_AI_BASE_URL` | 空 | Client 侧自定义或 OpenAI-compatible 基地址 |

---

## 数据库

### PostgreSQL（生产环境）

Gateway 启动时会自动执行 `CREATE TABLE IF NOT EXISTS` 建表，无需手动初始化。

只需确保：
1. PostgreSQL 实例已运行且可达
2. 目标数据库已创建（如 `CREATE DATABASE jarvis;`）
3. 连接用户有建表权限

```bash
# 示例：创建数据库
psql -U postgres -c "CREATE DATABASE jarvis;"
psql -U postgres -c "CREATE USER jarvis WITH PASSWORD 'your-password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE jarvis TO jarvis;"

# 配置连接
export DATABASE_URL=postgresql://jarvis:your-password@localhost:5432/jarvis
```

### SQLite（开发/测试）

不设置 `DATABASE_URL` 或设为文件路径即可，数据文件自动创建：

```bash
# 以下三种写法均可
export DATABASE_URL=sqlite:///gateway/gateway.db
export DATABASE_URL=gateway/gateway.db
# 或不设置，使用默认值
```

---

## Dashboard 管理面板

Dashboard 不再由 Gateway 直接渲染页面，而是作为独立静态前端部署。

本地开发：

```bash
cd dashboard
npm install
npm run dev
```

生产部署：

```bash
cd dashboard
VITE_GATEWAY_BASE_URL=/jarvis/api npm run build
```

容器镜像构建：

```bash
docker build -f dashboard/Dockerfile \
  --build-arg VITE_GATEWAY_BASE_URL=/jarvis/api \
  -t open-jarvis-dashboard .
```

部署参考见：

- `dashboard/README.md`
- `dashboard/DEPLOYMENT.md`

### 功能

| 模块 | 说明 |
|------|------|
| 概览 | 在线设备数、App 连接数、Skill 数量、任务状态分布 |
| 设备管理 | 添加/删除设备，查看连接状态和最后活跃时间，管理设备 Skill |
| Skill 管理 | 系统预置 `shell/docker/process/filesystem` builtin skills，自定义 Skill 支持 zip 归档上传与分配 |
| 任务监控 | 按状态/设备筛选任务，查看任务详情和日志 |
| 系统设置 | 查看数据库连接、JWT 配置、已注册设备列表 |

### 认证

- Dashboard 静态页面可由 Nginx 或任意静态文件服务公开托管
- 所有 API 请求需要 JWT Token（登录后自动附带）
- 登录凭证与 Gateway 管理员账号相同
- Token 有效期 12 小时，过期后自动跳回登录页

---

## API 端点

### 认证

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/auth/login` | 无 | 登录获取 JWT |

### 任务管理（App 使用）

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/tasks` | Bearer | 创建任务 |
| GET | `/tasks/{task_id}` | Bearer | 查询任务 |
| GET | `/tasks/pending_approvals` | Bearer | 待审批列表 |
| POST | `/tasks/{task_id}/decision` | Bearer | 审批决策 |
| GET | `/devices` | Bearer | 设备列表 |

补充说明：

- `POST /tasks` 仍然支持显式传入 `device_id`
- 当不传 `device_id` 时，Gateway 会使用自身 AI 配置在已注册 CLI 与 `gateway-local` 本机执行端之间做自动路由

### WebSocket

| 路径 | 认证 | 说明 |
|------|------|------|
| `/ws/app?token=<jwt>` | JWT | App 实时推送（TASK_SNAPSHOT, TASK_LOG） |
| `/ws/client?device_id=<id>&timestamp=<ts>&signature=<sig>` | HMAC-SHA256 | 设备连接 |

### Dashboard API（`/dashboard/api/*`，全部需要 Bearer Token）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dashboard/api/overview` | 系统概览统计 |
| GET/POST | `/dashboard/api/devices` | 设备列表 / 创建设备 |
| GET/PUT/DELETE | `/dashboard/api/devices/{id}` | 设备详情 / 修改 / 删除 |
| GET/POST | `/dashboard/api/skills` | Skill 列表 / 创建 |
| GET/PUT/DELETE | `/dashboard/api/skills/{id}` | Skill 详情 / 修改 / 删除 |
| GET/POST | `/dashboard/api/devices/{id}/skills` | 设备 Skill 列表 / 分配 |
| DELETE | `/dashboard/api/devices/{id}/skills/{sid}` | 移除设备 Skill |
| GET | `/dashboard/api/tasks` | 任务列表（支持 ?status=&device_id=&limit=） |
| GET | `/dashboard/api/system` | 系统信息 |
| PUT/DELETE | `/dashboard/api/ai/gateway` | 写入 / 清除 Gateway AI 覆盖配置（不提供读接口） |
| PUT/DELETE | `/dashboard/api/ai/devices/{id}` | 写入 / 清除指定 CLI 的 AI 覆盖配置（不提供读接口） |

---

## Builtin Skills

Gateway 启动后会自动注册以下可直接分配的 builtin skills：

- `builtin-shell`: Linux Shell 命令执行，始终要求审批
- `builtin-docker`: Docker 容器查询与重启，重启动作要求审批
- `builtin-process`: 系统负载与高占用进程查看
- `builtin-filesystem`: 允许目录下的文件读取与后缀搜索

这些 builtin skills 不需要上传 zip。分配到设备后，Gateway 会通过 `DEVICE_SKILLS_SYNC` 下发 action 元数据，Client 只向 AI 暴露当前已启用的 builtin actions。

自定义 archive skills 仍沿用 zip 归档流程，用于同步运行手册、脚本或后续扩展能力目录。

---

## 测试

```bash
# 全部测试（使用 SQLite，无需 PostgreSQL）
pytest -q

# 仅 gateway
pytest gateway/tests/ -v

# Dashboard 构建
cd dashboard && npm run build

# Flutter
cd app && flutter test
```

---

## Docker 说明

- 仓库内置的 `docker-compose.yml` 已包含 `postgres`、`gateway`、`client`、`dashboard` 四个服务
- `dashboard/Dockerfile` 使用多阶段构建：Node 负责编译前端，Nginx 负责静态分发与 `/jarvis/api` 反代
- Gateway 容器负责 API、WebSocket 与 `gateway-local` 本机执行端
- Gateway 与 Client 都会只读挂载整个仓库到 `/workspace`，供文件系统技能访问
- Gateway 与 Client 都挂载 `/var/run/docker.sock`，以便 Docker 技能执行容器查询与重启
- `gateway_data`、`client_data`、`postgres_data` 三个 volume 会持久化审批状态、技能归档、checkpoint 与数据库
- 国内网络可把 `.env` 里的 `CLIENT_DOCKERFILE` 改成 `client/Dockerfile.cn`，切到内置的 apt/pip 镜像加速版
- 若需接入外部 PostgreSQL，只需在 `.env` 中显式设置 `DATABASE_URL`

示例：

```bash
CLIENT_DOCKERFILE=client/Dockerfile.cn docker compose build client
```

### 健康检查

- Gateway: `GET /health` → `{"status": "ok"}`
- Dashboard: `GET /health` → `ok`
- Gateway / Client / Dashboard Dockerfile 均内置 healthcheck（30s 间隔）

---

## 默认凭证（仅开发环境）

| 项目 | 值 |
|------|-----|
| 管理员账号 | `operator` |
| 管理员密码 | `passw0rd` |
| 设备 ID | `device-alpha` |
| 设备密钥 | `device-secret` |

> **生产环境务必修改 `OMNI_AGENT_JWT_SECRET`、`OMNI_AGENT_ADMIN_PASSWORD` 和设备密钥。**
