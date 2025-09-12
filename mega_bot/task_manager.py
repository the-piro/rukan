"""Task management for download tracking and coordination."""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from .logger import LOGGER


class TaskState(Enum):
    """Task states."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Information about a download task."""
    gid: str
    link: str
    name: str
    state: TaskState
    status_obj: Optional[object] = None
    error: Optional[str] = None


class TaskManager:
    """Manages download tasks and their states."""
    
    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, TaskInfo] = {}
        self.download_queue = asyncio.Queue()
        self.active_downloads = 0
        self.lock = asyncio.Lock()
        self._workers_started = False
    
    async def add_task(self, gid: str, link: str, name: str) -> None:
        """Add a new task to the manager."""
        async with self.lock:
            task_info = TaskInfo(
                gid=gid,
                link=link,
                name=name,
                state=TaskState.QUEUED
            )
            self.tasks[gid] = task_info
            await self.download_queue.put(gid)
            LOGGER.info(f"Added task {gid}: {name}")
    
    async def update_task_status(self, gid: str, status_obj: object) -> None:
        """Update task with status object."""
        async with self.lock:
            if gid in self.tasks:
                self.tasks[gid].status_obj = status_obj
                if self.tasks[gid].state == TaskState.QUEUED:
                    self.tasks[gid].state = TaskState.RUNNING
    
    async def complete_task(self, gid: str) -> None:
        """Mark task as completed."""
        async with self.lock:
            if gid in self.tasks:
                self.tasks[gid].state = TaskState.COMPLETED
                self.active_downloads = max(0, self.active_downloads - 1)
                LOGGER.info(f"Task {gid} completed")
    
    async def fail_task(self, gid: str, error: str) -> None:
        """Mark task as failed."""
        async with self.lock:
            if gid in self.tasks:
                self.tasks[gid].state = TaskState.FAILED
                self.tasks[gid].error = error
                self.active_downloads = max(0, self.active_downloads - 1)
                LOGGER.error(f"Task {gid} failed: {error}")
    
    async def cancel_task(self, gid: str) -> bool:
        """Cancel a task."""
        async with self.lock:
            if gid not in self.tasks:
                return False
            
            task = self.tasks[gid]
            if task.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
                return False
            
            task.state = TaskState.CANCELLED
            
            # If task has status object with cancel method, call it
            if hasattr(task.status_obj, 'cancel_task'):
                try:
                    await task.status_obj.cancel_task()
                except Exception as e:
                    LOGGER.error(f"Error cancelling task {gid}: {e}")
            
            if task.state == TaskState.RUNNING:
                self.active_downloads = max(0, self.active_downloads - 1)
            
            LOGGER.info(f"Task {gid} cancelled")
            return True
    
    def get_task(self, gid: str) -> Optional[TaskInfo]:
        """Get task information."""
        return self.tasks.get(gid)
    
    def get_active_tasks(self) -> List[TaskInfo]:
        """Get all active (queued or running) tasks."""
        return [
            task for task in self.tasks.values()
            if task.state in (TaskState.QUEUED, TaskState.RUNNING)
        ]
    
    def get_recent_tasks(self, limit: int = 5) -> List[TaskInfo]:
        """Get recently completed/failed tasks."""
        completed_tasks = [
            task for task in self.tasks.values()
            if task.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED)
        ]
        # Return most recent (this is simple since we don't have timestamps)
        return completed_tasks[-limit:] if completed_tasks else []
    
    async def start_workers(self):
        """Start background workers to process download queue."""
        if self._workers_started:
            return
        
        self._workers_started = True
        
        for i in range(self.max_concurrent):
            asyncio.create_task(self._download_worker(f"worker-{i}"))
        
        LOGGER.info(f"Started {self.max_concurrent} download workers")
    
    async def _download_worker(self, worker_name: str):
        """Background worker to process downloads."""
        LOGGER.info(f"Download worker {worker_name} started")
        
        while True:
            try:
                # Get next download from queue
                gid = await self.download_queue.get()
                
                async with self.lock:
                    if gid not in self.tasks:
                        continue
                    
                    task = self.tasks[gid]
                    if task.state != TaskState.QUEUED:
                        continue
                    
                    self.active_downloads += 1
                    task.state = TaskState.RUNNING
                
                LOGGER.info(f"Worker {worker_name} starting download {gid}")
                
                # Import here to avoid circular imports
                from mega_bot.mega.downloader import start_mega_download
                
                try:
                    await start_mega_download(task.link, gid, self)
                except Exception as e:
                    await self.fail_task(gid, str(e))
                
            except Exception as e:
                LOGGER.error(f"Download worker {worker_name} error: {e}")
                await asyncio.sleep(1)


# Global task manager instance
task_manager = TaskManager()