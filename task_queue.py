"""
Task queue manager with Redis support (optional) and in-memory fallback
"""
import asyncio
import logging
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """Represents a pipeline task"""
    
    def __init__(
        self,
        task_id: str,
        task_type: str,
        payload: Dict[str, Any],
        priority: int = 0
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result
        }


class InMemoryQueue:
    """In-memory task queue implementation"""
    
    def __init__(self):
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.tasks: Dict[str, Task] = {}
        self.lock = asyncio.Lock()
    
    async def enqueue(self, task: Task) -> None:
        """Add task to queue"""
        async with self.lock:
            self.tasks[task.task_id] = task
            # Use negative priority for max-heap behavior
            await self.queue.put((-task.priority, task.task_id, task))
            logger.info(f"Task {task.task_id} enqueued (priority: {task.priority})")
    
    async def dequeue(self) -> Optional[Task]:
        """Get next task from queue"""
        try:
            _, task_id, task = await asyncio.wait_for(
                self.queue.get(),
                timeout=1.0
            )
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            return task
        except asyncio.TimeoutError:
            return None
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        async with self.lock:
            return self.tasks.get(task_id)
    
    async def update_task(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: str = None
    ) -> None:
        """Update task status"""
        async with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = status
                task.completed_at = datetime.now()
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
    
    async def get_queue_size(self) -> int:
        """Get number of pending tasks"""
        return self.queue.qsize()
    
    async def get_all_tasks(self) -> Dict[str, Task]:
        """Get all tasks"""
        async with self.lock:
            return self.tasks.copy()


class RedisQueue:
    """Redis-backed task queue (optional)"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.queue_key = "ls2clearml:task_queue"
        self.tasks_key = "ls2clearml:tasks"
    
    async def enqueue(self, task: Task) -> None:
        """Add task to Redis queue"""
        # Store task data
        task_data = json.dumps(task.to_dict())
        await self.redis.hset(self.tasks_key, task.task_id, task_data)
        
        # Add to priority queue (sorted set)
        await self.redis.zadd(
            self.queue_key,
            {task.task_id: -task.priority}  # Negative for max-heap
        )
        logger.info(f"Task {task.task_id} enqueued to Redis (priority: {task.priority})")
    
    async def dequeue(self) -> Optional[Task]:
        """Get next task from Redis queue"""
        # Get highest priority task
        result = await self.redis.zpopmax(self.queue_key)
        
        if not result:
            return None
        
        task_id = result[0][0].decode('utf-8')
        
        # Get task data
        task_data = await self.redis.hget(self.tasks_key, task_id)
        if not task_data:
            return None
        
        task_dict = json.loads(task_data)
        
        # Reconstruct task
        task = Task(
            task_id=task_dict['task_id'],
            task_type=task_dict['task_type'],
            payload=task_dict['payload'],
            priority=task_dict['priority']
        )
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now()
        
        # Update in Redis
        await self.redis.hset(self.tasks_key, task_id, json.dumps(task.to_dict()))
        
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID from Redis"""
        task_data = await self.redis.hget(self.tasks_key, task_id)
        if not task_data:
            return None
        
        task_dict = json.loads(task_data)
        task = Task(
            task_id=task_dict['task_id'],
            task_type=task_dict['task_type'],
            payload=task_dict['payload'],
            priority=task_dict['priority']
        )
        task.status = TaskStatus(task_dict['status'])
        return task
    
    async def update_task(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: str = None
    ) -> None:
        """Update task status in Redis"""
        task = await self.get_task(task_id)
        if task:
            task.status = status
            task.completed_at = datetime.now()
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            
            await self.redis.hset(
                self.tasks_key,
                task_id,
                json.dumps(task.to_dict())
            )
    
    async def get_queue_size(self) -> int:
        """Get number of pending tasks in Redis"""
        return await self.redis.zcard(self.queue_key)


class TaskQueueManager:
    """Manages task queuing and processing"""
    
    def __init__(self, use_redis: bool = False, redis_url: str = None):
        self.use_redis = use_redis
        self.queue = None
        self.redis_client = None
        self.handlers: Dict[str, Callable] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        
        if use_redis and redis_url:
            try:
                import redis.asyncio as aioredis
                self.redis_client = aioredis.from_url(redis_url)
                self.queue = RedisQueue(self.redis_client)
                logger.info("Using Redis-backed task queue")
            except ImportError:
                logger.warning("Redis not available, falling back to in-memory queue")
                self.queue = InMemoryQueue()
        else:
            self.queue = InMemoryQueue()
            logger.info("Using in-memory task queue")
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a task handler"""
        self.handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """Submit a new task to the queue"""
        task_id = f"{task_type}_{datetime.now().timestamp()}"
        task = Task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority
        )
        
        await self.queue.enqueue(task)
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = await self.queue.get_task(task_id)
        return task.to_dict() if task else None
    
    async def _worker(self, worker_id: int):
        """Worker coroutine to process tasks"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get next task
                task = await self.queue.dequeue()
                
                if task is None:
                    await asyncio.sleep(0.1)
                    continue
                
                logger.info(f"Worker {worker_id} processing task {task.task_id}")
                
                # Get handler
                handler = self.handlers.get(task.task_type)
                
                if handler is None:
                    error_msg = f"No handler registered for task type: {task.task_type}"
                    logger.error(error_msg)
                    await self.queue.update_task(
                        task.task_id,
                        TaskStatus.FAILED,
                        error=error_msg
                    )
                    continue
                
                # Execute handler
                try:
                    result = await handler(task.payload)
                    await self.queue.update_task(
                        task.task_id,
                        TaskStatus.COMPLETED,
                        result=result
                    )
                    logger.info(f"Task {task.task_id} completed successfully")
                    
                except Exception as e:
                    error_msg = f"Task {task.task_id} failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    await self.queue.update_task(
                        task.task_id,
                        TaskStatus.FAILED,
                        error=error_msg
                    )
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                await asyncio.sleep(1.0)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start(self, num_workers: int = 3):
        """Start task queue workers"""
        if self.running:
            logger.warning("Task queue already running")
            return
        
        self.running = True
        logger.info(f"Starting task queue with {num_workers} workers")
        
        # Start workers
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        
        logger.info(f"Task queue started with {num_workers} workers")
    
    async def stop(self):
        """Stop task queue workers"""
        if not self.running:
            return
        
        logger.info("Stopping task queue...")
        self.running = False
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers.clear()
        
        # Close Redis connection if used
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Task queue stopped")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        all_tasks = await self.queue.get_all_tasks() if isinstance(self.queue, InMemoryQueue) else {}
        
        pending = sum(1 for t in all_tasks.values() if t.status == TaskStatus.PENDING)
        processing = sum(1 for t in all_tasks.values() if t.status == TaskStatus.PROCESSING)
        completed = sum(1 for t in all_tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in all_tasks.values() if t.status == TaskStatus.FAILED)
        
        return {
            "queue_size": await self.queue.get_queue_size(),
            "total_tasks": len(all_tasks),
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "workers": len(self.workers),
            "running": self.running
        }


# Global task queue instance
_task_queue = None


def get_task_queue(use_redis: bool = False, redis_url: str = None) -> TaskQueueManager:
    """Get or create global task queue"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueueManager(use_redis=use_redis, redis_url=redis_url)
    return _task_queue
