# OpenJarvis Dashboard

独立前端控制台，使用 `npm` 构建为静态资源，产物输出到 `dist/`。

## 开发

```bash
npm install
npm run dev
```

## 构建

```bash
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

## 子路径与 Nginx 部署

将 `dist/` 部署到 Nginx 静态目录，并把 `/auth/` 与 `/dashboard/api/` 反代到网关。
可参考：

- [nginx.conf.example](/home/coder/project/open-jarvis/dashboard/nginx.conf.example)
- [DEPLOYMENT.md](/home/coder/project/open-jarvis/dashboard/DEPLOYMENT.md)
