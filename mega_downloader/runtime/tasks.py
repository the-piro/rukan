import asyncio

task_dict = {}
# Protect multi-task mutation (future: queue, concurrency limits)
task_dict_lock = asyncio.Lock()

class QueueStatus:
    def __init__(self, name: str, gid: str, kind: str):
        self.name = name
        self.gid = gid
        self.kind = kind