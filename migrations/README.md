# Migrations

Alembic 数据库迁移目录。

- `env.py`：迁移环境配置，从应用配置读取 `DATABASE_URL`。
- `script.py.mako`：迁移脚本模板。
- `versions/`：存放生成的迁移版本文件。

常用命令：

```bash
# 生成迁移（自动检测模型变更）
uv run alembic revision --autogenerate -m "create agent tables"

# 执行迁移
uv run alembic upgrade head

# 回滚一个版本
uv run alembic downgrade -1
```
