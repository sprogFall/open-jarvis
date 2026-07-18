"""数据访问层：PostgreSQL / Redis 访问。

对应架构设计第 8 节持久化与恢复。PostgreSQL 是事实源，Redis 只承担队列、缓存、
取消标记和低延迟事件流，丢失后可由数据库恢复。
"""

__all__: list[str] = []
