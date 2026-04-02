# Omni-Agent

初始化实现包含四个模块：

- `gateway`: FastAPI 网关，负责任务状态、审批持久化、JWT 与设备鉴权、WebSocket 路由。
- `dashboard`: 独立静态前端项目，负责设备/Skill/任务管理，可通过 `npm build` 输出 `dist/` 并部署到 Nginx。
- `client`: Python 执行端，基于 LangGraph 驱动规划/执行/审批中断恢复，负责技能执行、本地 checkpoint、日志脱敏。
- `app`: Flutter 控制端，负责待审批恢复、任务派发、命令预览与实时日志工作台。

---

## 快速开始

### 前置依赖

- Python 3.11+
- PostgreSQL 14+（生产环境）
- Docker & Docker Compose（容器部署）
- Flutter 3.x（移动端开发）

### 本地开发（SQLite）

不配置 `DATABASE_URL` 时自动使用 SQLite，无需 PostgreSQL：

```bash
pip install -r gateway/requirements.txt
pytest -q                          # 运行测试
uvicorn gateway.main:app --reload  # 启动开发服务器
```

如需启动 Dashboard 前端：

```bash
cd dashboard
npm install
npm run dev
```

### 容器部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DATABASE_URL 等

# 2. 启动
docker compose up --build -d

# 3. 运行 Flutter 端
cd app && flutter run
```

---

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABASE_URL` | 生产必填 | `sqlite:///gateway/gateway.db` | 数据库连接地址。生产用 `postgresql://user:pass@host:5432/dbname`，本地开发可不配（自动用 SQLite） |
| `OMNI_AGENT_GATEWAY_DB` | 否 | 无 | 旧版 SQLite 路径变量，当前仍兼容；仅当未设置 `DATABASE_URL` 时生效 |
| `OMNI_AGENT_JWT_SECRET` | **是** | `change-me-change-me-change-me-1234` | JWT 签名密钥，**生产环境必须修改**，建议 32 字符以上随机字符串 |
| `OMNI_AGENT_ADMIN_USERNAME` | 否 | `operator` | 管理员账号，用于登录 Dashboard 和 App |
| `OMNI_AGENT_ADMIN_PASSWORD` | **是** | `passw0rd` | 管理员密码，**生产环境必须修改** |
| `OMNI_AGENT_DEVICE_KEYS` | 否 | `device-alpha=device-secret` | 预注册设备，格式 `id1=key1,id2=key2`。也可通过 Dashboard 动态添加 |
| `OMNI_AGENT_DASHBOARD_ORIGINS` | 否 | 空 | 允许 Dashboard 跨域访问的 Origin 列表，逗号分隔，例如 `https://static.example.com` |
| `OMNI_AGENT_GATEWAY_AI_PROVIDER` | 否 | 空 | Gateway 侧 AI 供应商标识；若数据库已有覆盖配置，则数据库优先 |
| `OMNI_AGENT_GATEWAY_AI_MODEL` | 否 | 空 | Gateway 侧 AI 模型名 |
| `OMNI_AGENT_GATEWAY_AI_API_KEY` | 否 | 空 | Gateway 侧 AI Key |
| `OMNI_AGENT_GATEWAY_AI_BASE_URL` | 否 | 空 | 自定义或 OpenAI-compatible 网关地址 |
| `OMNI_AGENT_GATEWAY_ALLOWED_ROOTS` | 否 | 当前工作目录 | Gateway 本机执行时允许访问的文件根目录，使用 `:` 分隔 |

### Client 端环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OMNI_AGENT_GATEWAY_URL` | `http://gateway:8000` | Gateway 地址 |
| `OMNI_AGENT_DEVICE_ID` | `device-alpha` | 当前设备标识 |
| `OMNI_AGENT_DEVICE_KEY` | `device-secret` | 当前设备签名密钥，需与 Gateway 侧一致 |
| `OMNI_AGENT_CHECKPOINT_DB` | `/data/client/client.db` | Client checkpoint 存储路径 |
| `OMNI_AGENT_LANGGRAPH_DB` | `/data/client/langgraph.db` | LangGraph workflow 状态存储路径 |
| `OMNI_AGENT_ALLOWED_ROOTS` | `/workspace` | 文件系统技能允许访问的根目录 |
| `OMNI_AGENT_IOT_BASE_URL` | (空) | IoT 平台接口地址 |
| `OMNI_AGENT_IOT_TOKEN` | (空) | IoT 平台认证 Token |
| `OMNI_AGENT_CLIENT_AI_PROVIDER` | (空) | Client 侧 AI 供应商标识；若本地数据库已有覆盖配置，则本地数据库优先 |
| `OMNI_AGENT_CLIENT_AI_MODEL` | (空) | Client 侧 AI 模型名 |
| `OMNI_AGENT_CLIENT_AI_API_KEY` | (空) | Client 侧 AI Key |
| `OMNI_AGENT_CLIENT_AI_BASE_URL` | (空) | 自定义或 OpenAI-compatible 网关地址 |

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

部署参考见：

- `dashboard/README.md`
- `dashboard/DEPLOYMENT.md`

### 功能

| 模块 | 说明 |
|------|------|
| 概览 | 在线设备数、App 连接数、Skill 数量、任务状态分布 |
| 设备管理 | 添加/删除设备，查看连接状态和最后活跃时间，管理设备 Skill |
| Skill 管理 | 创建/编辑/删除 Skill，支持 JSON 配置 |
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

- Gateway 容器只负责 API 和 WebSocket，不再承载 Dashboard 页面
- Dashboard 推荐构建为静态资源后交给 Nginx 部署
- `client` 容器只读挂载整个仓库到 `/workspace`，供文件系统技能访问
- `client` 容器挂载 `/var/run/docker.sock`，以便 Docker 技能执行容器查询与重启
- PostgreSQL 需自行部署或使用外部实例，通过 `DATABASE_URL` 连接

### 健康检查

- Gateway: `GET /health` → `{"status": "ok"}`
- Dockerfile 内置 healthcheck（30s 间隔）

---

## 默认凭证（仅开发环境）

| 项目 | 值 |
|------|-----|
| 管理员账号 | `operator` |
| 管理员密码 | `passw0rd` |
| 设备 ID | `device-alpha` |
| 设备密钥 | `device-secret` |

> **生产环境务必修改 `OMNI_AGENT_JWT_SECRET`、`OMNI_AGENT_ADMIN_PASSWORD` 和设备密钥。**
