#!/usr/bin/env python3
"""
Task Automation Workflow
Manages tasks, reminders, and productivity automation
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import redis
import hashlib
from enum import Enum

# Windmill imports
import wmill

class TaskPriority(Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskAutomation:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://ollama:11434')
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
        self.vikunja_url = os.getenv('VIKUNJA_URL', 'http://vikunja:3456')
        self.vikunja_token = os.getenv('VIKUNJA_API_TOKEN', '')

    async def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None,
        labels: List[str] = None,
        project: str = "default",
        user_id: str = "default"
    ) -> Dict:
        """Create a new task"""
        task_id = hashlib.md5(
            f"{title}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        task = {
            'id': task_id,
            'title': title,
            'description': description,
            'priority': priority,
            'status': TaskStatus.TODO.value,
            'due_date': due_date or (datetime.now() + timedelta(days=7)).isoformat(),
            'labels': labels or [],
            'project': project,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'user_id': user_id
        }

        # Store in Redis
        task_key = f'task:{user_id}:{task_id}'
        self.redis_client.setex(task_key, 2592000, json.dumps(task))  # 30 days TTL

        # Add to user's task list
        task_list_key = f'tasks:{user_id}'
        self.redis_client.lpush(task_list_key, task_id)

        # If Vikunja is configured, sync there
        if self.vikunja_token:
            await self._sync_to_vikunja(task)

        # Store in vector DB for semantic search
        await self._store_task_embedding(task)

        return task

    async def _sync_to_vikunja(self, task: Dict) -> bool:
        """Sync task to Vikunja"""
        if not self.vikunja_token:
            return False

        async with aiohttp.ClientSession() as session:
            try:
                headers = {'Authorization': f'Bearer {self.vikunja_token}'}
                vikunja_task = {
                    'title': task['title'],
                    'description': task['description'],
                    'priority': self._map_priority_to_vikunja(task['priority']),
                    'due_date': task['due_date'],
                    'labels': task['labels']
                }

                async with session.post(
                    f'{self.vikunja_url}/api/v1/lists/1/tasks',
                    json=vikunja_task,
                    headers=headers
                ) as resp:
                    return resp.status == 201
            except Exception as e:
                print(f"Vikunja sync error: {e}")
                return False

    def _map_priority_to_vikunja(self, priority: str) -> int:
        """Map priority to Vikunja's numeric system"""
        mapping = {
            'urgent': 5,
            'high': 4,
            'medium': 3,
            'low': 2
        }
        return mapping.get(priority, 3)

    async def _store_task_embedding(self, task: Dict) -> bool:
        """Store task in vector database for semantic search"""
        async with aiohttp.ClientSession() as session:
            try:
                # Create searchable text
                task_text = f"{task['title']} {task['description']} {' '.join(task['labels'])}"

                # Get embedding
                embed_payload = {
                    'model': 'all-minilm',
                    'prompt': task_text
                }
                async with session.post(f'{self.ollama_url}/api/embeddings', json=embed_payload) as resp:
                    if resp.status == 200:
                        embed_data = await resp.json()
                        embedding = embed_data.get('embedding')

                        # Ensure collection exists
                        await session.put(
                            f'{self.qdrant_url}/collections/tasks',
                            json={
                                'vectors': {
                                    'size': 384,
                                    'distance': 'Cosine'
                                }
                            }
                        )

                        # Store the task
                        store_payload = {
                            'points': [{
                                'id': task['id'],
                                'vector': embedding,
                                'payload': task
                            }]
                        }

                        async with session.put(
                            f'{self.qdrant_url}/collections/tasks/points',
                            json=store_payload
                        ) as store_resp:
                            return store_resp.status == 200
            except Exception as e:
                print(f"Embedding storage error: {e}")
                return False

    async def update_task_status(
        self,
        task_id: str,
        new_status: str,
        user_id: str = "default"
    ) -> Dict:
        """Update task status"""
        task_key = f'task:{user_id}:{task_id}'
        task_data = self.redis_client.get(task_key)

        if not task_data:
            return {'error': 'Task not found'}

        task = json.loads(task_data)
        task['status'] = new_status
        task['updated_at'] = datetime.now().isoformat()

        # Add status transition to history
        if 'history' not in task:
            task['history'] = []
        task['history'].append({
            'timestamp': datetime.now().isoformat(),
            'action': 'status_change',
            'from': task.get('status'),
            'to': new_status
        })

        # Update in Redis
        self.redis_client.setex(task_key, 2592000, json.dumps(task))

        return task

    async def get_tasks(
        self,
        user_id: str = "default",
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project: Optional[str] = None
    ) -> List[Dict]:
        """Get tasks with optional filters"""
        task_list_key = f'tasks:{user_id}'
        task_ids = self.redis_client.lrange(task_list_key, 0, -1)

        tasks = []
        for task_id in task_ids:
            task_key = f'task:{user_id}:{task_id}'
            task_data = self.redis_client.get(task_key)
            if task_data:
                task = json.loads(task_data)

                # Apply filters
                if status and task['status'] != status:
                    continue
                if priority and task['priority'] != priority:
                    continue
                if project and task['project'] != project:
                    continue

                tasks.append(task)

        # Sort by priority and due date
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        tasks.sort(key=lambda x: (
            priority_order.get(x['priority'], 4),
            x['due_date']
        ))

        return tasks

    async def search_tasks(self, query: str, user_id: str = "default", limit: int = 10) -> List[Dict]:
        """Search tasks using semantic search"""
        async with aiohttp.ClientSession() as session:
            try:
                # Get embedding for query
                embed_payload = {
                    'model': 'all-minilm',
                    'prompt': query
                }
                async with session.post(f'{self.ollama_url}/api/embeddings', json=embed_payload) as resp:
                    if resp.status == 200:
                        embed_data = await resp.json()
                        embedding = embed_data.get('embedding')

                        # Search in Qdrant
                        search_payload = {
                            'vector': embedding,
                            'limit': limit,
                            'with_payload': True,
                            'filter': {
                                'must': [
                                    {'key': 'user_id', 'match': {'value': user_id}}
                                ]
                            }
                        }

                        async with session.post(
                            f'{self.qdrant_url}/collections/tasks/points/search',
                            json=search_payload
                        ) as search_resp:
                            if search_resp.status == 200:
                                search_data = await search_resp.json()
                                return [
                                    {**r['payload'], 'score': r['score']}
                                    for r in search_data.get('result', [])
                                ]
            except Exception as e:
                print(f"Search error: {e}")

        return []

    async def generate_task_recommendations(self, user_id: str = "default") -> Dict:
        """Generate AI-powered task recommendations"""
        # Get current tasks
        tasks = await self.get_tasks(user_id)

        # Analyze task patterns
        task_summary = {
            'total': len(tasks),
            'by_status': {},
            'by_priority': {},
            'overdue': 0
        }

        now = datetime.now()
        for task in tasks:
            # Count by status
            status = task['status']
            task_summary['by_status'][status] = task_summary['by_status'].get(status, 0) + 1

            # Count by priority
            priority = task['priority']
            task_summary['by_priority'][priority] = task_summary['by_priority'].get(priority, 0) + 1

            # Check overdue
            due_date = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
            if due_date < now and task['status'] != TaskStatus.DONE.value:
                task_summary['overdue'] += 1

        # Generate AI recommendations
        async with aiohttp.ClientSession() as session:
            try:
                prompt = f"""Based on this task analysis, provide 3-5 specific recommendations:

Total tasks: {task_summary['total']}
By status: {task_summary['by_status']}
By priority: {task_summary['by_priority']}
Overdue: {task_summary['overdue']}

Recent tasks: {[t['title'] for t in tasks[:5]]}

Provide actionable recommendations for task management and productivity."""

                payload = {
                    'model': os.getenv('DEFAULT_LLM_MODEL', 'llama3.2:latest'),
                    'prompt': prompt,
                    'stream': False
                }

                async with session.post(f'{self.ollama_url}/api/generate', json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        recommendations = data.get('response', 'No recommendations available')
                    else:
                        recommendations = "AI recommendations unavailable"
            except Exception as e:
                print(f"AI recommendation error: {e}")
                recommendations = "Error generating recommendations"

        return {
            'summary': task_summary,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }

    async def create_recurring_task(
        self,
        title: str,
        description: str,
        frequency: str,  # daily, weekly, monthly
        priority: str = "medium",
        user_id: str = "default"
    ) -> Dict:
        """Create a recurring task"""
        # Create the initial task
        task = await self.create_task(
            title=f"[Recurring] {title}",
            description=description,
            priority=priority,
            user_id=user_id
        )

        # Store recurring configuration
        recurring_key = f'recurring:{user_id}:{task["id"]}'
        recurring_config = {
            'task_template': task,
            'frequency': frequency,
            'next_occurrence': self._calculate_next_occurrence(frequency),
            'active': True
        }
        self.redis_client.set(recurring_key, json.dumps(recurring_config))

        return {
            'task': task,
            'recurring': recurring_config
        }

    def _calculate_next_occurrence(self, frequency: str) -> str:
        """Calculate next occurrence based on frequency"""
        now = datetime.now()
        if frequency == 'daily':
            next_date = now + timedelta(days=1)
        elif frequency == 'weekly':
            next_date = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            next_date = now + timedelta(days=30)
        else:
            next_date = now + timedelta(days=1)

        return next_date.isoformat()

@wmill.main()
async def main(
    action: str,
    user_id: str = "default",
    **kwargs
):
    """
    Main entry point for task automation workflow

    Args:
        action: Action to perform (create, update, list, search, recommend, recurring)
        user_id: User identifier
        **kwargs: Additional parameters based on action

    Returns:
        Result of the requested action
    """
    automation = TaskAutomation()

    if action == "create":
        return await automation.create_task(
            title=kwargs.get('title'),
            description=kwargs.get('description', ''),
            priority=kwargs.get('priority', 'medium'),
            due_date=kwargs.get('due_date'),
            labels=kwargs.get('labels', []),
            project=kwargs.get('project', 'default'),
            user_id=user_id
        )

    elif action == "update_status":
        return await automation.update_task_status(
            task_id=kwargs.get('task_id'),
            new_status=kwargs.get('status'),
            user_id=user_id
        )

    elif action == "list":
        return await automation.get_tasks(
            user_id=user_id,
            status=kwargs.get('status'),
            priority=kwargs.get('priority'),
            project=kwargs.get('project')
        )

    elif action == "search":
        return await automation.search_tasks(
            query=kwargs.get('query'),
            user_id=user_id,
            limit=kwargs.get('limit', 10)
        )

    elif action == "recommend":
        return await automation.generate_task_recommendations(user_id)

    elif action == "recurring":
        return await automation.create_recurring_task(
            title=kwargs.get('title'),
            description=kwargs.get('description', ''),
            frequency=kwargs.get('frequency', 'daily'),
            priority=kwargs.get('priority', 'medium'),
            user_id=user_id
        )

    else:
        return {'error': f'Unknown action: {action}'}

# For testing locally
if __name__ == "__main__":
    import asyncio
    # Example: Create a task
    result = asyncio.run(main(
        action="create",
        title="Test task",
        description="This is a test task"
    ))
    print(json.dumps(result, indent=2))
