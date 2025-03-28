import os
from typing import Dict, Any, List, Optional
import openai
from datetime import datetime
from .data_store import ProjectDataStore

class TaskManager:
    """Manages project tasks with DeepSeek API integration."""

    def __init__(self, data_store: Optional[ProjectDataStore] = None):
        """Initialize the task manager."""
        self.data_store = data_store or ProjectDataStore()
        self.setup_deepseek()

    def setup_deepseek(self):
        """Configure DeepSeek API client."""
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")
        
        openai.api_key = api_key
        openai.api_base = "https://api.deepseek.com/v1"

    async def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """Analyze a task using DeepSeek API."""
        try:
            response = await openai.ChatCompletion.acreate(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a project management assistant. Analyze the following task and provide structured information about its requirements, dependencies, and estimated complexity."
                    },
                    {
                        "role": "user",
                        "content": task_description
                    }
                ]
            )
            
            analysis = response.choices[0].message.content
            return {
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise RuntimeError(f"Failed to analyze task with DeepSeek API: {str(e)}")

    async def create_task(self, title: str, description: str, priority: str = "medium") -> str:
        """Create a new task with AI analysis."""
        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Analyze task with DeepSeek
        analysis = await self.analyze_task(f"{title}\n\n{description}")
        
        task_data = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "analysis": analysis
        }
        
        self.data_store.save_task(task_id, task_data)
        return task_id

    def update_task_status(self, task_id: str, status: str, progress_notes: Optional[str] = None):
        """Update task status and add progress notes."""
        task = self.data_store.load_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        task["status"] = status
        task["updated_at"] = datetime.utcnow().isoformat()
        
        if progress_notes:
            if "progress_history" not in task:
                task["progress_history"] = []
            
            task["progress_history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "notes": progress_notes
            })
        
        self.data_store.save_task(task_id, task)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task details by ID."""
        return self.data_store.load_task(task_id)

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tasks, optionally filtered by status."""
        tasks = []
        for task_id in self.data_store.list_files('tasks'):
            task = self.data_store.load_task(task_id)
            if task and (not status or task.get('status') == status):
                tasks.append(task)
        return tasks

    async def generate_task_summary(self) -> Dict[str, Any]:
        """Generate a summary of all tasks using DeepSeek API."""
        tasks = self.list_tasks()
        if not tasks:
            return {"summary": "No tasks found"}

        try:
            task_data = "\n".join([
                f"Task: {t['title']}\nStatus: {t['status']}\nPriority: {t['priority']}"
                for t in tasks
            ])

            response = await openai.ChatCompletion.acreate(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a project management assistant. Generate a summary of the following tasks, including progress overview and key metrics."
                    },
                    {
                        "role": "user",
                        "content": f"Tasks to analyze:\n{task_data}"
                    }
                ]
            )
            
            return {
                "summary": response.choices[0].message.content,
                "task_count": len(tasks),
                "status_breakdown": {
                    status: len([t for t in tasks if t.get('status') == status])
                    for status in {'created', 'in_progress', 'completed'}
                },
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise RuntimeError(f"Failed to generate task summary: {str(e)}")