"""
Database operations for task management
"""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from .task_models import Task, TaskStatus, TaskPriority


class TaskManager:
    """Manages task CRUD operations with JSON file storage"""
    
    def __init__(self, file_path: str = "data/tasks.json"):
        self.file_path = file_path
        self.ensure_file_exists()
    
    def ensure_file_exists(self) -> None:
        """Ensure the tasks JSON file exists"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
    
    def create_task(self, task: Task) -> bool:
        """Create a new task"""
        try:
            tasks = self.get_all_tasks_raw()
            task_dict = task.model_dump()
            tasks.append(task_dict)
            return self._save_tasks(tasks)
        except Exception as e:
            print(f"Error creating task: {e}")
            return False
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks as Task objects"""
        try:
            tasks_data = self.get_all_tasks_raw()
            return [Task(**task_data) for task_data in tasks_data]
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
    
    def get_all_tasks_raw(self) -> List[Dict[str, Any]]:
        """Get all tasks as raw dictionaries"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading tasks file: {e}")
            return []
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        try:
            tasks = self.get_all_tasks()
            for task in tasks:
                if task.id == task_id:
                    return task
            return None
        except Exception as e:
            print(f"Error getting task by ID: {e}")
            return None
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a task by ID"""
        try:
            tasks = self.get_all_tasks_raw()
            for task in tasks:
                if task['id'] == task_id:
                    task.update(updates)
                    task['updated_at'] = datetime.now().isoformat()
                    return self._save_tasks(tasks)
            return False
        except Exception as e:
            print(f"Error updating task: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID"""
        try:
            tasks = self.get_all_tasks_raw()
            original_count = len(tasks)
            tasks = [t for t in tasks if t['id'] != task_id]
            if len(tasks) < original_count:
                return self._save_tasks(tasks)
            return False
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False
    
    def delete_tasks_by_date(self, target_date: str) -> int:
        """Delete all tasks for a specific date. Returns count of deleted tasks."""
        try:
            tasks = self.get_all_tasks_raw()
            original_count = len(tasks)
            tasks = [t for t in tasks if t.get('date') != target_date]
            deleted_count = original_count - len(tasks)
            
            if deleted_count > 0:
                self._save_tasks(tasks)
            
            return deleted_count
        except Exception as e:
            print(f"Error deleting tasks by date: {e}")
            return 0
    
    def get_tasks_by_date(self, target_date: str) -> List[Task]:
        """Get tasks for a specific date (YYYY-MM-DD)"""
        try:
            all_tasks = self.get_all_tasks()
            return [task for task in all_tasks if task.date == target_date]
        except Exception as e:
            print(f"Error getting tasks by date: {e}")
            return []
    
    def check_time_conflict(self, date: str, start_time: str, exclude_task_id: str = None) -> List[Task]:
        """Check for conflicting tasks at the same date and time"""
        try:
            date_tasks = self.get_tasks_by_date(date)
            conflicting_tasks = []
            
            for task in date_tasks:
                # Skip the task we're updating if provided
                if exclude_task_id and task.id == exclude_task_id:
                    continue
                    
                # Check if there's a time conflict
                if task.start_time == start_time:
                    conflicting_tasks.append(task)
            
            return conflicting_tasks
        except Exception as e:
            print(f"Error checking time conflict: {e}")
            return []
    
    def find_task_to_move(self, date: str, start_time: str, title_hint: str = None) -> Optional[Task]:
        """Find a task to move based on date, time, and optional title hint"""
        try:
            date_tasks = self.get_tasks_by_date(date)
            
            # First, try to find exact time match
            time_matches = [task for task in date_tasks if task.start_time == start_time]
            
            if not time_matches:
                return None
            
            # If no title hint, return first match
            if not title_hint:
                return time_matches[0]
            
            # Try to find best match with title hint
            title_hint_lower = title_hint.lower()
            for task in time_matches:
                if title_hint_lower in task.title.lower():
                    return task
            
            # Return first match if no title match
            return time_matches[0]
        except Exception as e:
            print(f"Error finding task to move: {e}")
            return None
    
    def postpone_tasks_by_date(self, from_date: str, to_date: str) -> int:
        """Move all tasks from one date to another. Returns count of moved tasks."""
        try:
            tasks = self.get_all_tasks_raw()
            moved_count = 0
            
            # Check for conflicts in the target date first
            target_tasks = self.get_tasks_by_date(to_date)
            target_times = {task.start_time for task in target_tasks if task.start_time}
            
            for task in tasks:
                if task.get('date') == from_date:
                    # Check if this task's time conflicts with existing tasks on target date
                    task_time = task.get('start_time')
                    if task_time and task_time in target_times:
                        print(f"Warning: Task '{task.get('title')}' at {task_time} conflicts with existing task on {to_date}")
                        # Still move it, but note the conflict
                    
                    task['date'] = to_date
                    task['updated_at'] = datetime.now().isoformat()
                    moved_count += 1
            
            if moved_count > 0:
                self._save_tasks(tasks)
            
            return moved_count
        except Exception as e:
            print(f"Error postponing tasks by date: {e}")
            return 0
    
    def get_today_tasks(self) -> List[Task]:
        """Get today's tasks"""
        today = date.today().isoformat()
        return self.get_tasks_by_date(today)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by status"""
        try:
            all_tasks = self.get_all_tasks()
            return [task for task in all_tasks if task.status == status]
        except Exception as e:
            print(f"Error getting tasks by status: {e}")
            return []
    
    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title or description"""
        try:
            all_tasks = self.get_all_tasks()
            query_lower = query.lower()
            return [
                task for task in all_tasks 
                if query_lower in task.title.lower() or 
                   query_lower in (task.description or "").lower()
            ]
        except Exception as e:
            print(f"Error searching tasks: {e}")
            return []
    
    def get_task_count(self) -> int:
        """Get total number of tasks"""
        return len(self.get_all_tasks_raw())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task statistics"""
        try:
            tasks = self.get_all_tasks()
            total = len(tasks)
            
            if total == 0:
                return {
                    "total": 0,
                    "pending": 0,
                    "completed": 0,
                    "cancelled": 0,
                    "today": 0
                }
            
            pending = len([t for t in tasks if t.status == TaskStatus.PENDING])
            completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            cancelled = len([t for t in tasks if t.status == TaskStatus.CANCELLED])
            today = len(self.get_today_tasks())
            
            return {
                "total": total,
                "pending": pending,
                "completed": completed,
                "cancelled": cancelled,
                "today": today
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total": 0, "pending": 0, "completed": 0, "cancelled": 0, "today": 0}
    
    def _save_tasks(self, tasks: List[Dict[str, Any]]) -> bool:
        """Save tasks to JSON file"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(tasks, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving tasks: {e}")
            return False


# Global task manager instance
task_manager = TaskManager()


def get_task_manager() -> TaskManager:
    """Get the global task manager instance"""
    return task_manager