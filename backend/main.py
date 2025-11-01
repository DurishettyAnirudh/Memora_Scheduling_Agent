"""
FastAPI backend for the scheduling agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from agents.scheduler_agent import create_scheduling_agent
from data.database import get_task_manager
from data.task_models import Task
from config.settings import API_HOST, API_PORT, CORS_ORIGINS
from routes.document_routes import documents_router


app = FastAPI(
    title="Local Scheduling Agent API",
    description="A fully local scheduling agent with natural language processing",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent and task manager
scheduling_agent = create_scheduling_agent()
task_manager = get_task_manager()

# Include document routes
app.include_router(documents_router)


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(message: ChatMessage):
    """Main chat endpoint for interacting with scheduling agent"""
    try:
        initial_state = {
            "messages": [{"role": "user", "content": message.message}],
            "current_task": None,
            "task_operation": None,
            "task_data": None,
            "response": None,
            "error": None
        }
        
        final_state = scheduling_agent.invoke(initial_state)
        
        return ChatResponse(response=final_state.get("response", "Sorry, I couldn't process that request."))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/tasks")
async def get_all_tasks():
    """Get all tasks for calendar display"""
    try:
        tasks = task_manager.get_all_tasks_raw()
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")


@app.get("/tasks/today")
async def get_today_tasks():
    """Get today's tasks"""
    try:
        today_tasks = task_manager.get_today_tasks()
        tasks_data = [task.model_dump() for task in today_tasks]
        return {"tasks": tasks_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching today's tasks: {str(e)}")


@app.get("/tasks/stats")
async def get_task_stats():
    """Get task statistics"""
    try:
        stats = task_manager.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.get("/tasks/search/{query}")
async def search_tasks(query: str):
    """Search tasks by query"""
    try:
        tasks = task_manager.search_tasks(query)
        tasks_data = [task.model_dump() for task in tasks]
        return {"tasks": tasks_data, "query": query, "count": len(tasks_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching tasks: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from config.model_manager import get_model_manager
        model_manager = get_model_manager()
        
        stats = task_manager.get_stats()
        
        return {
            "status": "healthy",
            "model": model_manager.get_current_model(),
            "model_ready": model_manager.is_ready(),
            "tasks_total": stats["total"],
            "tasks_today": stats["today"]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Local Scheduling Agent API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat (POST)",
            "tasks": "/tasks (GET)",
            "today": "/tasks/today (GET)",
            "stats": "/tasks/stats (GET)",
            "search": "/tasks/search/{query} (GET)",
            "health": "/health (GET)",
            "documents": "/documents (GET, POST)",
            "document_search": "/documents/search (POST, GET)",
            "document_upload": "/documents/upload (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)