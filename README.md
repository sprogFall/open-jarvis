# Omni-Agent

初始化实现包含三个模块：

- `gateway`: FastAPI 网关，负责任务状态、审批持久化、JWT 与设备鉴权、WebSocket 路由。
- `client`: Python 执行端，基于 LangGraph 驱动规划/执行/审批中断恢复，负责技能执行、本地 checkpoint、日志脱敏。
- `app`: Flutter 控制端，负责待审批恢复、任务派发、命令预览与实时日志工作台。

## 本地测试

```bash
pytest -q
cd app && flutter test
```

## 容器启动

1. 复制环境变量样例：

```bash
cp .env.example .env
```

2. 启动网关与客户端：

```bash
docker compose up --build
```

3. 运行 Flutter 端：

```bash
cd app
flutter run
```

默认情况下：

- 网关监听 `http://127.0.0.1:8000`
- Flutter 端默认登录账号为 `operator / passw0rd`
- 客户端设备标识为 `device-alpha`

## Docker 说明

- `gateway` 容器把 SQLite 数据持久化到 `gateway_data`。
- `client` 容器把 checkpoint 与 LangGraph workflow 状态都持久化到 `client_data`。
- `client` 容器只读挂载整个仓库到 `/workspace`，供文件系统技能访问。
- `client` 容器挂载 `/var/run/docker.sock`，以便 Docker 技能执行容器查询与重启。
