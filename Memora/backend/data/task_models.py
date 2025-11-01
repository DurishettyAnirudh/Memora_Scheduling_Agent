"""
Task data models and structures
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=1000)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    start_time: Optional[str] = Field(default=None, description="Time in HH:MM format")
    end_time: Optional[str] = Field(default=None, description="Time in HH:MM format")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now().isoformat()

    class Config:
        use_enum_values = True