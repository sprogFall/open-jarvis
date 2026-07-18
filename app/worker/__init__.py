"""Worker：队列消费、恢复、心跳。

对应架构设计第 8.2 节。Worker 使用 run_id 作为 LangGraph thread_id，
进程异常后由租约/心跳回收运行，读取最近 Checkpoint 继续。
"""

__all__: list[str] = []
