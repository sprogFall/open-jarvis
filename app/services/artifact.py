"""Artifact 服务：大对象产物存储引用管理。

小型结构化结果保存在 PostgreSQL jsonb；确有文件或大文本场景时再接入
S3/MinIO 兼容对象存储，数据库只保留引用。
"""

from __future__ import annotations


__all__: list[str] = []
