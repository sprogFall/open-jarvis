# Dashboard 子路径部署参考

本文档覆盖两类部署方式：

1. 直接使用仓库根目录的 `docker-compose.yml` 一键启动完整容器栈
2. 单独构建 Dashboard 静态资源 / `dashboard/Dockerfile`，再接入已有 Gateway

当前前端构建已经满足以下场景：

- 静态资源使用相对路径输出，适合挂到 `/jarvis/dashboard` 这类子路径
- API 基地址通过 `VITE_GATEWAY_BASE_URL` 配置
- 当 `VITE_GATEWAY_BASE_URL=/jarvis/api` 时，前端会请求：
  - `/jarvis/api/auth/login`
  - `/jarvis/api/dashboard/api/overview`
  - `/jarvis/api/dashboard/api/devices`

另外，Skills 管理分为 builtin 与 archive 两类：

- builtin skills 由 Gateway 自动注册，不需要额外归档目录
- archive skills 依赖 Gateway 的归档目录与 Client 的本地技能工作目录
- Gateway 需要可写的 `OMNI_AGENT_SKILL_ARCHIVES_DIR`，用于保存上传的 zip 归档
- Client 可通过 `OMNI_AGENT_SKILLS_WORKSPACE` 指定技能解压目录

## 1. 用 docker compose 一键启动

仓库已经内置完整容器编排：

- `postgres`
- `gateway`
- `client`
- `dashboard`

启动步骤：

```bash
cp .env.example .env
# 修改 JWT、管理员密码、设备密钥、数据库密码

docker compose up --build -d
```

如果希望用交互式方式补全 `.env` 并直接启动，推荐在仓库根目录执行 Bash 脚本：

```bash
./jarvisctl
# 或直接一键部署
./jarvisctl deploy
```

部署助手会：

- 检查 `.env` 是否存在
- 对缺失项或示例默认值做命令行引导输入
- 自动把结果写回 `.env`
- 自动同步 Gateway 设备注册表与 Client 设备身份
- 支持按需部署 `postgres`、`gateway`、`client`、`dashboard` 任意单端或组合
- 单独部署时会强制校验外部依赖地址，避免误用 Compose 内部默认地址

例如：

```bash
./jarvisctl deploy postgres
./jarvisctl deploy gateway
./jarvisctl deploy postgres gateway
./jarvisctl deploy dashboard
./jarvisctl deploy client
./jarvisctl deploy
DEPLOY_NETWORK_PROFILE=cn ./jarvisctl deploy dashboard
```

其中：

```bash
./jarvisctl deploy gateway
# docker compose up -d --build --no-deps gateway
# 需要在 .env 中填写 DATABASE_URL

./jarvisctl deploy dashboard
# docker compose up -d --build --no-deps dashboard
# 需要在 .env 中填写绝对地址 VITE_GATEWAY_BASE_URL

./jarvisctl deploy client
# docker compose up -d --build --no-deps client
# 需要在 .env 中填写可从容器访问的远端 OMNI_AGENT_GATEWAY_URL

./jarvisctl deploy postgres gateway
# docker compose up -d --build postgres gateway
```

如果是国内网络，推荐把 `.env` 里的 `DEPLOY_NETWORK_PROFILE=cn`。脚本会自动切换：

- `gateway/Dockerfile.cn`
- `client/Dockerfile.cn`
- `dashboard/Dockerfile.cn`
- Dashboard npm registry: `https://registry.npmmirror.com`

但基础镜像下载仍依赖宿主机 Docker 自身的 registry mirror；如果服务器拉取 `node` / `nginx` / `python` / `postgres` 很慢，需要同时配置 Docker daemon 镜像加速。

其中：

- `dashboard` 服务由 `dashboard/Dockerfile` 构建
- Dashboard 默认监听宿主机 `8080` 端口
- Gateway 默认监听宿主机 `8000` 端口
- 浏览器访问地址为 `http://localhost:8080/jarvis/dashboard/`
- Dashboard 会把 `/jarvis/api/*` 反代到 `gateway:8000`

如需只重建 Dashboard：

```bash
docker compose build dashboard
docker compose up -d --no-deps dashboard
```

## 2. 单独构建 Dashboard 镜像

如果你已经有现成 Gateway，只想单独构建 Dashboard 容器：

```bash
docker build -f dashboard/Dockerfile \
  --build-arg VITE_GATEWAY_BASE_URL=/jarvis/api \
  -t open-jarvis-dashboard .
```

镜像内置的 Nginx 配置文件为：

- `dashboard/nginx.conf`
- `dashboard/nginx.conf.example`

## 3. 单独构建静态资源

在 `dashboard/` 目录执行：

```bash
npm install
VITE_GATEWAY_BASE_URL=/jarvis/api npm run build
```

构建产物在：

```text
dashboard/dist/
```

## 4. Nginx 路由建议

如果同域部署，建议把静态站点和 API 都挂到统一域名：

- Dashboard: `/jarvis/dashboard`
- Gateway: `/jarvis/api`

示例：

```nginx
server {
    listen 80;
    server_name xx.com;

    location = / {
        return 302 /jarvis/dashboard/;
    }

    location = /jarvis/dashboard {
        return 301 /jarvis/dashboard/;
    }

    location /jarvis/dashboard/ {
        alias /srv/open-jarvis/dashboard/dist/;
        index index.html;
        try_files $uri $uri/ /jarvis/dashboard/index.html;
    }

    location /jarvis/api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

关键点：

- `location /jarvis/api/` 配合 `proxy_pass http://127.0.0.1:8000/;` 会把 `/jarvis/api/...` 映射成网关实际收到的 `/...`
- 因此前端访问 `/jarvis/api/auth/login` 时，网关仍然命中自身的 `/auth/login`
- 同理 `/jarvis/api/dashboard/api/tasks` 会命中网关的 `/dashboard/api/tasks`
- WebSocket 也会沿用同一条 `/jarvis/api` 反代链路

## 5. 如果 Dashboard 与 Gateway 不同域

如果 Dashboard 运行在 `https://static.example.com/jarvis/dashboard`，Gateway 运行在 `https://gateway.example.com/jarvis/api`：

构建时设置：

```bash
VITE_GATEWAY_BASE_URL=https://gateway.example.com/jarvis/api npm run build
```

同时在 Gateway 端配置允许的跨域来源，例如：

```bash
OMNI_AGENT_DASHBOARD_ORIGINS=https://static.example.com
```

当前网关会把该配置写入 CORS 中间件。

## 6. Skills 归档存储

如果希望把 Skills 归档放到独立目录，可在 Gateway 环境变量中设置：

```bash
OMNI_AGENT_SKILL_ARCHIVES_DIR=/srv/open-jarvis/data/skill-archives
```

Client 侧可设置：

```bash
OMNI_AGENT_SKILLS_WORKSPACE=/srv/open-jarvis/client/skills-runtime
```

这样，设备拿到分配后的 skill 时，会自动解压到：

```text
/srv/open-jarvis/client/skills-runtime/<skill_id>/
```

## 7. 登录与接口路径映射

前端固定调用这两组逻辑路径：

- `/auth/login`
- `/dashboard/api/*`

它们都会自动拼到 `VITE_GATEWAY_BASE_URL` 后面。

示例：

| `VITE_GATEWAY_BASE_URL` | 登录接口 | 设备列表接口 |
| --- | --- | --- |
| 空 | `/auth/login` | `/dashboard/api/devices` |
| `/jarvis/api` | `/jarvis/api/auth/login` | `/jarvis/api/dashboard/api/devices` |
| `https://gw.example.com/jarvis/api` | `https://gw.example.com/jarvis/api/auth/login` | `https://gw.example.com/jarvis/api/dashboard/api/devices` |

## 8. 部署检查清单

上线前建议确认：

1. 访问 `https://xx.com/jarvis/dashboard/` 能返回 `index.html`
2. 浏览器网络面板中，登录请求发往 `https://xx.com/jarvis/api/auth/login`
3. 设备列表请求发往 `https://xx.com/jarvis/api/dashboard/api/devices`
4. 如果跨域部署，响应里存在正确的 `Access-Control-Allow-Origin`
5. nginx 对 `/jarvis/dashboard/` 使用 `try_files` 回退到 `index.html`
6. Gateway 进程对 `OMNI_AGENT_SKILL_ARCHIVES_DIR` 目录有写权限
7. Client 进程对 `OMNI_AGENT_SKILLS_WORKSPACE` 目录有写权限
8. 如果使用仓库自带容器编排，`docker compose ps` 中 `postgres/gateway/client/dashboard` 全部为 healthy 或 running
