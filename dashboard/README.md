# OpenJarvis Dashboard

独立前端控制台，使用 `npm run build` 产出静态资源到 `dist/`，也提供 `dashboard/Dockerfile` 直接构建容器镜像。

当前 Skills 流程分为两类：

- builtin skills：Gateway 启动后自动提供，可直接分配给设备，分配后会直接暴露给 AI 规划器
- archive skills：上传 zip 归档 -> Gateway 保存归档 -> 设备分配后自动下载并解压到本地工作目录

archive skills 仍需满足以下约束：

- zip 内必须包含 `SKILL.md`
- 可以直接压缩单个 skill 文件夹，也可以上传包含 skill 子目录的开源仓库片段
- 设备收到分配后，会把 skill 解压到 `OMNI_AGENT_SKILLS_WORKSPACE/<skill_id>/`

## 开发

```bash
npm install
npm run dev
```

## 本地构建

```bash
npm install
npm run build
```

默认通过相对路径访问网关：

- `POST /auth/login`
- `GET /dashboard/api/*`

如果网关被反代到子路径，比如 `https://xx.com/jarvis/api`，构建前设置：

```bash
VITE_GATEWAY_BASE_URL=/jarvis/api npm run build
```

如果静态站点与网关不在同域，也可以设置完整地址：

```bash
VITE_GATEWAY_BASE_URL=https://gateway.example.com/jarvis/api npm run build
```

## 容器镜像构建

直接在仓库根目录执行：

```bash
docker build -f dashboard/Dockerfile \
  --build-arg VITE_GATEWAY_BASE_URL=/jarvis/api \
  -t open-jarvis-dashboard .
```

容器内置 Nginx 配置会：

- 提供 `/jarvis/dashboard/` 静态页面
- 反代 `/jarvis/api/*` 到 `gateway:8000`
- 兼容 WebSocket 升级头

如果直接使用仓库自带编排，执行：

```bash
docker compose up --build -d dashboard gateway
```

默认访问：

- `http://localhost:8080/jarvis/dashboard/`
- `http://localhost:8080/jarvis/api/auth/login`

## 子路径与 Nginx 部署

仓库提供两份可直接参考的配置：

- `dashboard/nginx.conf`
- `dashboard/nginx.conf.example`

完整部署说明见：

- `dashboard/DEPLOYMENT.md`
