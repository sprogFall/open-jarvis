# Dashboard 子路径部署参考

本文档覆盖两类部署目标：

1. Dashboard 静态资源部署在 `https://xx.com/jarvis/dashboard`
2. Gateway API 通过反代暴露为 `https://xx.com/jarvis/api`

当前前端构建已经满足这类场景：

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
- 设备分配 Skill 后，会通过网关同步归档元数据，再按需下载 zip 并解压成文件夹

## 1. 构建

在 `dashboard/` 目录执行：

```bash
npm install
VITE_GATEWAY_BASE_URL=/jarvis/api npm run build
```

构建产物在：

```text
dashboard/dist/
```

## 2. Nginx 路由建议

如果同域部署，建议把静态站点和 API 都挂到统一域名：

- Dashboard: `/jarvis/dashboard`
- Gateway: `/jarvis/api`

示例：

```nginx
server {
    listen 80;
    server_name xx.com;

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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

关键点：

- `location /jarvis/api/` 配合 `proxy_pass http://127.0.0.1:8000/;` 会把 `/jarvis/api/...` 映射成网关实际收到的 `/...`
- 因此前端访问 `/jarvis/api/auth/login` 时，网关仍然命中自身的 `/auth/login`
- 同理 `/jarvis/api/dashboard/api/tasks` 会命中网关的 `/dashboard/api/tasks`

## 3. 如果 Dashboard 与 Gateway 不同域

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

## 4. Skills 归档存储

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

## 5. 登录与接口路径映射

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

## 6. 部署检查清单

上线前建议确认：

1. 访问 `https://xx.com/jarvis/dashboard/` 能返回 `index.html`
2. 浏览器网络面板中，登录请求发往 `https://xx.com/jarvis/api/auth/login`
3. 设备列表请求发往 `https://xx.com/jarvis/api/dashboard/api/devices`
4. 如果跨域部署，响应里存在正确的 `Access-Control-Allow-Origin`
5. nginx 对 `/jarvis/dashboard/` 使用 `try_files` 回退到 `index.html`
6. Gateway 进程对 `OMNI_AGENT_SKILL_ARCHIVES_DIR` 目录有写权限
7. Client 进程对 `OMNI_AGENT_SKILLS_WORKSPACE` 目录有写权限
