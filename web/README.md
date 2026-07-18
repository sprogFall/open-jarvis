# Web 前端

此目录用于 Open Jarvis 的前端页面。

后端 API 与 SSE 事件协议见架构设计第 9 节，前端通过 `/api/v1` 访问后端。

建议技术栈（后续初始化时选定）：
- React / Next.js / Vue 等任一现代框架
- 通过 SSE（`GET /api/v1/runs/{run_id}/events`）订阅实时进度

初始化示例（以 Vite + React 为例）：

```bash
cd web
npm create vite@latest . -- --template react-ts
npm install
npm run dev
```

开发时可配置代理将 `/api` 转发到后端 `http://localhost:8000`。
