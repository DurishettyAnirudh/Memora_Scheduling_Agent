# Local Scheduling Agent

A fully local scheduling agent built with FastAPI, LangChain, LangGraph, and Next.js.

## 🎬 Demo Video

https://github.com/DurishettyAnirudh/Memora_Scheduling_Agent/blob/main/Memora_Agent%20-%20Made%20with%20Clipchamp.mp4

<video width="100%" controls autoplay loop>
  <source src="Memora_Agent - Made with Clipchamp.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Hardware Requirements
- RTX 3050 4GB or better
- Ryzen 7 5800H or equivalent

## Tech Stack
- **Backend**: FastAPI + LangChain + LangGraph + Ollama
- **Frontend**: Next.js + React + FullCalendar + Tailwind CSS  
- **LLM**: Qwen 2.5 7B (via Ollama)

## Setup Instructions

### Prerequisites
1. Install [Ollama](https://ollama.ai/)
2. Install Python 3.10+
3. Install Node.js 18+

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

### 🚀 Quick Start

#### Option 1: One-Click Startup (Recommended)
```bash
# Run the all-in-one startup script
start_all.bat
```

#### Option 2: Manual Startup
1. **Start Ollama and Setup Model**
   ```bash
   # Start Ollama service
   ollama serve
   
   # Pull the recommended model for RTX 3050
   ollama pull qwen2.5:7b
   ```

2. **Start the Backend**
   ```bash
   cd backend
   start_backend.bat
   # OR manually: .venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

3. **Start the Frontend**
   ```bash
   cd frontend
   start_frontend.bat
   # OR manually: npm run dev
   ```

#### 🌐 Access Your Application
- **Chat Interface**: http://localhost:3000/chat
- **Calendar View**: http://localhost:3000/calendar  
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

### 💬 Usage Examples
Once running, try these commands in the chat:
- `"Schedule meeting tomorrow at 3pm"`
- `"Create doctor appointment next Friday at 10am"`
- `"Show my tasks"`
- `"Find meeting tasks"`

## Features
- Natural language task creation and management
- Interactive chat interface
- Calendar view with task visualization
- Fully local operation (no external APIs)
- Swappable LLM models