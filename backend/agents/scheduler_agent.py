"""
LangGraph-based scheduling agent
"""

import json
import uuid
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from langgraph.graph import StateGraph, END, START
from langchain_ollama import OllamaLLM

from config.model_manager import get_model_manager
from data.database import get_task_manager
from data.task_models import Task, TaskStatus, TaskPriority
from agents.document_enhancement import get_document_enhancement


class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    current_task: Optional[Dict[str, Any]]
    task_operation: Optional[str]  # create, read, update, delete, list
    task_data: Optional[Dict[str, Any]]
    response: Optional[str]
    error: Optional[str]
    conversation_context: Optional[Dict[str, Any]]  # Track recent topics and entities
    document_context: Optional[Dict[str, Any]]  # Document awareness context


def llm_node(state: AgentState) -> AgentState:
    """Process user input with LLM to understand intent"""
    try:
        model_manager = get_model_manager()
        
        last_message = state["messages"][-1]["content"]
        
        # Get current date for context
        today = date.today()
        tomorrow = date(today.year, today.month, today.day + 1) if today.day < 28 else date(today.year, today.month + 1, 1)
        
        # Get conversation context from recent messages
        context_info = ""
        if len(state["messages"]) > 1:
            recent_messages = state["messages"][-3:]  # Last 3 messages for context
            context_info = f"\nRecent conversation context:\n"
            for msg in recent_messages[:-1]:  # Exclude current message
                context_info += f"- {msg['role']}: {msg['content'][:100]}...\n"
        
        prompt = f"""You are Memora, a helpful AI assistant with advanced scheduling capabilities. 

Current date context:
- Today: {today.isoformat()} (Saturday: September 21, Sunday: September 22)
- Tomorrow: {tomorrow.isoformat()}
- Day after tomorrow: 2025-09-16

IMPORTANT: Parse dates intelligently:
- "this saturday" = 2025-09-21 (next Saturday)
- "tomorrow" = {tomorrow.isoformat()}
- "day after tomorrow" = 2025-09-16
- When user says "reschedule it" or "schedule it", understand from context what "it" refers to

{context_info}

🔍 SCHEDULING vs CONVERSATION:
- SCHEDULE: Clear scheduling words ("schedule", "plan", "book", "remind me") + time/date
- SCHEDULE QUERIES: Questions about availability, schedule conflicts, what's planned
- CONVERSATION: Greetings, questions about capabilities, general discussion, advice requests

🎯 SMART INTENT RECOGNITION:
- "Will it be possible to..." → Check schedule first, then respond about availability
- "I want all day tomorrow" → User wants time blocked/free, not a "free time" task
- "cancel all my meetings" → Filter by task type, only delete meetings/appointments
- "delete all meetings day after tomorrow" → Filter by type AND date

Current user request: {last_message}

Respond with JSON format only (no additional text):

For AVAILABILITY/FEASIBILITY QUERIES:
- "Will it be possible with tomorrows schedule to go to a trip?" → {{"action": "list_date", "date": "{tomorrow.isoformat()}", "query_type": "availability_check"}}
- "Am I free tomorrow afternoon?" → {{"action": "list_date", "date": "{tomorrow.isoformat()}", "query_type": "availability_check"}}

For TASK CREATION (only when user wants to schedule something):
{{"action": "create", "task_data": {{"title": "actual task name", "date": "YYYY-MM-DD", "start_time": "HH:MM or null", "priority": "low|medium|high"}}}}

For BULK TASK CREATION (multiple tasks with time patterns):
- "create 6 tasks for tomorrow starting from 3 pm with a gap of 1 hour" → {{"action": "create_bulk", "task_data": {{"count": 6, "title_base": "Task", "date": "{tomorrow.isoformat()}", "start_time": "15:00", "interval_minutes": 60}}}}
- "schedule 5 meetings today every 30 minutes starting at 9am" → {{"action": "create_bulk", "task_data": {{"count": 5, "title_base": "meeting", "date": "{today.isoformat()}", "start_time": "09:00", "interval_minutes": 30}}}}
- "create 3 appointments tomorrow at 10am, 2pm, and 4pm" → {{"action": "create", "task_data": [{{"title": "appointment", "date": "{tomorrow.isoformat()}", "start_time": "10:00"}}, {{"title": "appointment", "date": "{tomorrow.isoformat()}", "start_time": "14:00"}}, {{"title": "appointment", "date": "{tomorrow.isoformat()}", "start_time": "16:00"}}]}}

For VIEWING TASKS:
- "show tasks", "my schedule", "what do I have" → {{"action": "list"}}
- "tasks for tomorrow", "tomorrow's schedule" → {{"action": "list_date", "date": "{tomorrow.isoformat()}"}}
- "tasks for today", "today's schedule" → {{"action": "list_date", "date": "{today.isoformat()}"}}

For SEARCHING:
- "find meetings", "doctor appointments" → {{"action": "search", "query": "meeting"}}

For SELECTIVE DELETING (by task type):
- "cancel all my meetings tomorrow" → {{"action": "delete_selective", "date": "{tomorrow.isoformat()}", "task_type": "meeting"}}
- "delete all meetings day after tomorrow" → {{"action": "delete_selective", "date": "2025-09-16", "task_type": "meeting"}}
- "cancel all appointments today" → {{"action": "delete_selective", "date": "{today.isoformat()}", "task_type": "appointment"}}

For FULL DATE CLEARING:
- "delete all tasks for tomorrow", "clear tomorrow's schedule" → {{"action": "delete_date", "date": "{tomorrow.isoformat()}"}}
- "delete all tasks for today", "clear today" → {{"action": "delete_date", "date": "{today.isoformat()}"}}

For SINGLE TASK DELETION:
- "delete meeting", "remove task" → {{"action": "delete", "query": "meeting"}}

For MOVING/UPDATING TASKS:
- "move meeting at 3pm to 6pm", "reschedule meeting to tomorrow" → {{"action": "move", "task_data": {{"date": "YYYY-MM-DD", "old_time": "HH:MM", "new_time": "HH:MM", "title_hint": "meeting"}}}}
- "change meeting time to 4pm", "update appointment to Friday" → {{"action": "update", "task_data": {{"title_hint": "meeting or appointment", "new_date": "YYYY-MM-DD", "new_time": "HH:MM"}}}}
- "reschedule it to 9pm", "schedule it at 6pm" (when context is clear) → {{"action": "context_update", "task_data": {{"new_time": "HH:MM", "context_hint": "from recent conversation"}}}}

For BULK DATE CHANGES:
- "postpone all tasks for tomorrow to day after tomorrow" → {{"action": "postpone", "task_data": {{"from_date": "{tomorrow.isoformat()}", "to_date": "2025-09-16"}}}}
- "move all today's tasks to next week" → {{"action": "postpone", "task_data": {{"from_date": "{today.isoformat()}", "to_date": "2025-09-21"}}}}

For CONFLICT RESOLUTION:
- "replace the meeting with doctor appointment" → {{"action": "replace", "task_data": {{"old_title": "meeting", "new_title": "doctor appointment", "date": "YYYY-MM-DD", "time": "HH:MM"}}}}
- "cancel this", "never mind" → {{"action": "chat"}}

For CONVERSATION (greetings, questions, help):
- "hello", "hi", "how are you", "what can you do" → {{"action": "chat"}}

Examples:
✅ TASK CREATION:
- "Schedule meeting tomorrow at 3pm" → {{"action": "create", "task_data": {{"title": "meeting", "date": "{tomorrow.isoformat()}", "start_time": "15:00"}}}}
- "I have to go to saloon this saturday" → {{"action": "create", "task_data": {{"title": "go to saloon", "date": "2025-09-21", "start_time": null}}}}
- "Add doctor appointment Friday 10am" → {{"action": "create", "task_data": {{"title": "doctor appointment", "date": "2025-09-19", "start_time": "10:00"}}}}

✅ BULK TASK CREATION:
- "create 6 tasks for tomorrow starting from 3 pm with a gap of 1 hour" → {{"action": "create_bulk", "task_data": {{"count": 6, "title_base": "Task", "date": "{tomorrow.isoformat()}", "start_time": "15:00", "interval_minutes": 60}}}}
- "schedule 5 meetings today every 30 minutes starting at 9am" → {{"action": "create_bulk", "task_data": {{"count": 5, "title_base": "meeting", "date": "{today.isoformat()}", "start_time": "09:00", "interval_minutes": 30}}}}

✅ AVAILABILITY QUERIES:
- "Will it be possible with tomorrows schedule to go to a trip?" → {{"action": "list_date", "date": "{tomorrow.isoformat()}", "query_type": "availability_check"}}
- "Am I free tomorrow?" → {{"action": "list_date", "date": "{tomorrow.isoformat()}", "query_type": "availability_check"}}

✅ VIEWING/SEARCHING:
- "Show my tasks" → {{"action": "list"}}
- "What do I have tomorrow?" → {{"action": "list_date", "date": "{tomorrow.isoformat()}"}}
- "Find doctor appointments" → {{"action": "search", "query": "doctor"}}

✅ SELECTIVE DELETING:
- "Cancel all my meetings tomorrow" → {{"action": "delete_selective", "date": "{tomorrow.isoformat()}", "task_type": "meeting"}}
- "Delete all meetings day after tomorrow" → {{"action": "delete_selective", "date": "2025-09-16", "task_type": "meeting"}}
- "Cancel all appointments today" → {{"action": "delete_selective", "date": "{today.isoformat()}", "task_type": "appointment"}}

✅ FULL DATE CLEARING:
- "Delete all tasks for tomorrow" → {{"action": "delete_date", "date": "{tomorrow.isoformat()}"}}
- "Clear today's schedule" → {{"action": "delete_date", "date": "{today.isoformat()}"}}

✅ GLOBAL TASK DELETION:
- "Delete all tasks", "Clear all my tasks", "Remove everything" → {{"action": "delete_all"}}
- "Delete all the tasks I have on all days" → {{"action": "delete_all"}}

✅ SINGLE TASK DELETING:
- "Delete the meeting task" → {{"action": "delete", "query": "meeting"}}

✅ MOVING/UPDATING:
- "Move meeting at 15:00 to 6 pm" → {{"action": "move", "task_data": {{"date": "2025-09-16", "old_time": "15:00", "new_time": "18:00", "title_hint": "meeting"}}}}
- "Reschedule meeting with mila on day after tomorrow to 6 pm" → {{"action": "move", "task_data": {{"date": "2025-09-16", "old_time": "15:00", "new_time": "18:00", "title_hint": "meeting with mila"}}}}
- "Ok then schedule it at 9 pm" (when context = reschedule meeting with mila) → {{"action": "context_update", "task_data": {{"new_time": "21:00", "context_hint": "meeting with mila"}}}}

✅ BULK POSTPONING:
- "Postpone all tasks for tomorrow to day after tomorrow" → {{"action": "postpone", "task_data": {{"from_date": "{tomorrow.isoformat()}", "to_date": "2025-09-16"}}}}

✅ CONFLICT RESOLUTION:
- "Replace the meeting with gym session" → {{"action": "replace", "task_data": {{"old_title": "meeting", "new_title": "gym session", "date": "{tomorrow.isoformat()}", "time": "15:00"}}}}

✅ CONVERSATION:
- "Hello" → {{"action": "chat"}}
- "What can you help me with?" → {{"action": "chat"}}"""

        response = model_manager.invoke(prompt)
        
        if not response:
            state["error"] = "No response from LLM"
            return state
        
        # Try to extract JSON from response
        try:
            # Find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                parsed_response = json.loads(json_str)
                
                state["task_operation"] = parsed_response.get("action")
                state["task_data"] = parsed_response.get("task_data", {})
                state["current_task"] = parsed_response
            else:
                state["error"] = "Could not find JSON in LLM response"
                
        except json.JSONDecodeError as e:
            state["error"] = f"Failed to parse LLM response as JSON: {e}"
        
        # Add document context if relevant (non-disruptive)
        try:
            doc_enhancement = get_document_enhancement()
            operation = state.get("task_operation", "")
            
            if doc_enhancement.should_use_documents(last_message, operation):
                document_context = doc_enhancement.get_document_context(last_message)
                state["document_context"] = document_context
            
        except Exception as e:
            # Don't let document context errors affect core scheduling
            print(f"Document context error (non-critical): {e}")
            
    except Exception as e:
        state["error"] = f"Error in LLM node: {e}"
    
    return state


def task_operations_node(state: AgentState) -> AgentState:
    """Execute task operations based on LLM analysis"""
    try:
        task_manager = get_task_manager()
        operation = state.get("task_operation")
        
        if operation == "create":
            task_data = state["task_data"]
            
            # Handle both single task and multiple tasks
            if isinstance(task_data, list):
                # Multiple tasks creation
                created_tasks = []
                conflicts = []
                
                for single_task_data in task_data:
                    if not isinstance(single_task_data, dict):
                        continue
                        
                    # Ensure proper date format
                    task_date = single_task_data.get("date", date.today().isoformat())
                    
                    # Validate and fix date format if needed
                    try:
                        parsed_date = datetime.strptime(task_date, "%Y-%m-%d").date()
                        task_date = parsed_date.isoformat()
                    except ValueError:
                        task_date = date.today().isoformat()
                    
                    start_time = single_task_data.get("start_time")
                    
                    # Check for time conflicts if start_time is provided
                    if start_time:
                        conflicting_tasks = task_manager.check_time_conflict(task_date, start_time)
                        if conflicting_tasks:
                            conflicts.append({
                                "time": start_time,
                                "title": single_task_data.get("title", "Task"),
                                "conflicts": [task.title for task in conflicting_tasks]
                            })
                            continue
                    
                    # Create the task
                    task = Task(
                        title=single_task_data.get("title", "Untitled Task"),
                        description=single_task_data.get("description", ""),
                        date=task_date,
                        start_time=start_time,
                        end_time=single_task_data.get("end_time"),
                        priority=TaskPriority(single_task_data.get("priority", "medium"))
                    )
                    
                    if task_manager.create_task(task):
                        created_tasks.append(task)
                
                # Provide feedback
                if created_tasks and not conflicts:
                    task_list = []
                    for task in created_tasks:
                        time_info = f" at {task.start_time}" if task.start_time else ""
                        task_list.append(f"• {task.title}{time_info}")
                    
                    state["response"] = f"✅ Created {len(created_tasks)} tasks:\n" + "\n".join(task_list)
                elif created_tasks and conflicts:
                    task_list = []
                    for task in created_tasks:
                        time_info = f" at {task.start_time}" if task.start_time else ""
                        task_list.append(f"• {task.title}{time_info}")
                    
                    conflict_list = []
                    for conflict in conflicts:
                        conflict_list.append(f"• {conflict['title']} at {conflict['time']} (conflicts with: {', '.join(conflict['conflicts'])})")
                    
                    state["response"] = f"✅ Created {len(created_tasks)} tasks:\n" + "\n".join(task_list) + f"\n\n⚠️ Could not create {len(conflicts)} tasks due to conflicts:\n" + "\n".join(conflict_list)
                elif conflicts and not created_tasks:
                    conflict_list = []
                    for conflict in conflicts:
                        conflict_list.append(f"• {conflict['title']} at {conflict['time']} (conflicts with: {', '.join(conflict['conflicts'])})")
                    
                    state["response"] = f"⚠️ Could not create any tasks due to conflicts:\n" + "\n".join(conflict_list)
                else:
                    state["response"] = "❌ Failed to create tasks"
                    
            else:
                # Single task creation
                if not isinstance(task_data, dict):
                    state["response"] = "❌ Invalid task data format"
                    return state
                
                # Ensure proper date format
                task_date = task_data.get("date", date.today().isoformat())
                
                # Validate and fix date format if needed
                try:
                    parsed_date = datetime.strptime(task_date, "%Y-%m-%d").date()
                    task_date = parsed_date.isoformat()
                except ValueError:
                    task_date = date.today().isoformat()
                
                start_time = task_data.get("start_time")
                
                # Check for time conflicts if start_time is provided
                if start_time:
                    conflicting_tasks = task_manager.check_time_conflict(task_date, start_time)
                    if conflicting_tasks:
                        # Format conflict information
                        conflict_info = []
                        for task in conflicting_tasks:
                            conflict_info.append(f"• {task.title}")
                        
                        conflict_list = "\n".join(conflict_info)
                        date_name = "today" if task_date == date.today().isoformat() else "tomorrow" if task_date == (date.today() + timedelta(days=1)).isoformat() else task_date
                        
                        state["response"] = f"⚠️ **Time Conflict Detected!**\n\nThere's already a task scheduled for {date_name} at {start_time}:\n{conflict_list}\n\n🤔 **What would you like to do?**\n\nPlease choose an option:\n1️⃣ **Replace existing** - 'Replace the {conflicting_tasks[0].title} with {task_data.get('title')}'\n2️⃣ **Reschedule new task** - 'Schedule {task_data.get('title')} at [different time] instead'\n3️⃣ **Move existing task** - 'Move {conflicting_tasks[0].title} to [different time]'\n4️⃣ **Cancel** - 'Never mind, cancel this'\n\n💡 *Or just tell me what you'd prefer to do!*"
                        return state
                
                # No conflicts, create the task
                task = Task(
                    title=task_data.get("title", "Untitled Task"),
                    description=task_data.get("description", ""),
                    date=task_date,
                    start_time=start_time,
                    end_time=task_data.get("end_time"),
                    priority=TaskPriority(task_data.get("priority", "medium"))
                )
                
                success = task_manager.create_task(task)
                if success:
                    state["response"] = f"✅ Created task: '{task.title}' on {task.date}"
                    if task.start_time:
                        state["response"] += f" at {task.start_time}"
                else:
                    state["response"] = "❌ Failed to create task"
        
        elif operation == "create_bulk":
            task_data = state["task_data"]
            
            if not isinstance(task_data, dict):
                state["response"] = "❌ Invalid bulk task data format"
                return state
            
            count = task_data.get("count", 1)
            title_base = task_data.get("title_base", "Task")
            task_date = task_data.get("date", date.today().isoformat())
            start_time_str = task_data.get("start_time", "09:00")
            interval_minutes = task_data.get("interval_minutes", 60)
            
            # Validate date format
            try:
                parsed_date = datetime.strptime(task_date, "%Y-%m-%d").date()
                task_date = parsed_date.isoformat()
            except ValueError:
                task_date = date.today().isoformat()
            
            # Parse start time
            try:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
            except ValueError:
                start_time = datetime.strptime("09:00", "%H:%M").time()
            
            created_tasks = []
            conflicts = []
            
            # Create tasks with time intervals
            current_time = start_time
            for i in range(count):
                current_time_str = current_time.strftime("%H:%M")
                task_title = f"{title_base} {i + 1}" if count > 1 else title_base
                
                # Check for conflicts
                conflicting_tasks = task_manager.check_time_conflict(task_date, current_time_str)
                if conflicting_tasks:
                    conflicts.append({
                        "time": current_time_str,
                        "title": task_title,
                        "conflicts": [task.title for task in conflicting_tasks]
                    })
                else:
                    # Create the task
                    task = Task(
                        title=task_title,
                        description="",
                        date=task_date,
                        start_time=current_time_str,
                        end_time=None,
                        priority=TaskPriority("medium")
                    )
                    
                    if task_manager.create_task(task):
                        created_tasks.append(task)
                
                # Increment time for next task
                current_datetime = datetime.combine(date.today(), current_time)
                current_datetime += timedelta(minutes=interval_minutes)
                current_time = current_datetime.time()
            
            # Provide feedback
            date_name = "today" if task_date == date.today().isoformat() else "tomorrow" if task_date == (date.today() + timedelta(days=1)).isoformat() else task_date
            
            if created_tasks and not conflicts:
                task_list = []
                for task in created_tasks:
                    task_list.append(f"• {task.title} at {task.start_time}")
                
                state["response"] = f"✅ Created {len(created_tasks)} tasks for {date_name}:\n" + "\n".join(task_list)
            elif created_tasks and conflicts:
                task_list = []
                for task in created_tasks:
                    task_list.append(f"• {task.title} at {task.start_time}")
                
                conflict_list = []
                for conflict in conflicts:
                    conflict_list.append(f"• {conflict['title']} at {conflict['time']} (conflicts with: {', '.join(conflict['conflicts'])})")
                
                state["response"] = f"✅ Created {len(created_tasks)} tasks for {date_name}:\n" + "\n".join(task_list) + f"\n\n⚠️ Could not create {len(conflicts)} tasks due to conflicts:\n" + "\n".join(conflict_list)
            elif conflicts and not created_tasks:
                conflict_list = []
                for conflict in conflicts:
                    conflict_list.append(f"• {conflict['title']} at {conflict['time']} (conflicts with: {', '.join(conflict['conflicts'])})")
                
                state["response"] = f"⚠️ Could not create any tasks for {date_name} due to conflicts:\n" + "\n".join(conflict_list)
            else:
                state["response"] = "❌ Failed to create bulk tasks"
        
        elif operation == "list":
            tasks = task_manager.get_all_tasks()
            if tasks:
                task_list = []
                for task in tasks:
                    time_info = f" at {task.start_time}" if task.start_time else ""
                    status_emoji = "✅" if task.status == "completed" else "📋"
                    task_list.append(f"{status_emoji} {task.title} ({task.date}{time_info})")
                
                state["response"] = f"📅 Your tasks ({len(tasks)} total):\n" + "\n".join(task_list)
            else:
                state["response"] = "📅 No tasks found. Create your first task by saying something like 'Schedule meeting tomorrow at 3pm'!"
        
        elif operation == "list_date":
            target_date = state["current_task"].get("date")
            query_type = state["current_task"].get("query_type")
            
            if target_date:
                tasks = task_manager.get_tasks_by_date(target_date)
                date_name = "today" if target_date == date.today().isoformat() else "tomorrow" if target_date == (date.today() + timedelta(days=1)).isoformat() else target_date
                
                if query_type == "availability_check":
                    # Special handling for availability queries
                    if tasks:
                        task_list = []
                        for task in tasks:
                            time_info = f" at {task.start_time}" if task.start_time else ""
                            priority_emoji = "🔴" if task.priority == "high" else "🟡" if task.priority == "medium" else "🟢"
                            task_list.append(f"📋 {priority_emoji} {task.title}{time_info}")
                        
                        # Provide availability assessment
                        time_based_tasks = [t for t in tasks if t.start_time]
                        if time_based_tasks:
                            state["response"] = f"📅 **Your schedule for {date_name}** ({len(tasks)} tasks):\n" + "\n".join(task_list) + f"\n\n💭 **Availability Assessment:**\n{'🔴 **Busy day!**' if len(tasks) >= 4 else '🟡 **Moderately busy**' if len(tasks) >= 2 else '🟢 **Light schedule**'} You have {len(time_based_tasks)} timed task{'s' if len(time_based_tasks) != 1 else ''}.\n\n🗣️ Would you like me to help assess if a specific time slot works for your trip?"
                        else:
                            state["response"] = f"📅 **Your schedule for {date_name}** ({len(tasks)} tasks):\n" + "\n".join(task_list) + f"\n\n💭 **Good news!** All your tasks are flexible (no specific times), so you should have room for a trip! 🎒✈️"
                    else:
                        state["response"] = f"🎉 **Great news!** You're completely free {date_name}! Perfect day for a trip! 🎒✈️\n\n💡 Would you like me to block the time so you don't accidentally schedule anything?"
                else:
                    # Normal task listing
                    if tasks:
                        task_list = []
                        for task in tasks:
                            time_info = f" at {task.start_time}" if task.start_time else ""
                            status_emoji = "✅" if task.status == "completed" else "📋"
                            priority_emoji = "🔴" if task.priority == "high" else "🟡" if task.priority == "medium" else "🟢"
                            task_list.append(f"{status_emoji} {priority_emoji} {task.title}{time_info}")
                        
                        state["response"] = f"📅 Tasks for {date_name} ({len(tasks)} tasks):\n" + "\n".join(task_list)
                    else:
                        state["response"] = f"📅 No tasks scheduled for {date_name}. You're free!"
            else:
                state["response"] = "❌ Please specify a date"
        
        elif operation == "chat":
            # Use the full power of Qwen 2.5 7B for natural conversation
            user_message = state["messages"][-1]["content"]
            
            # Include document context if available
            document_info = ""
            if state.get("document_context") and state["document_context"].get("relevant_documents"):
                relevant_docs = state["document_context"]["relevant_documents"]
                if relevant_docs:
                    document_info = f"\n\nRELEVANT INFORMATION FROM YOUR DOCUMENTS:\n"
                    for doc in relevant_docs[:2]:  # Limit to top 2 documents
                        # Clean up the content snippet
                        content = doc.content_snippet.strip()
                        # Remove OCR artifacts and weird characters
                        content = content.replace('ÿþ', '').replace('ep CAMBRIDGE —', 'CAMBRIDGE').strip()
                        # Clean up multiple spaces and line breaks
                        content = ' '.join(content.split())
                        
                        if len(content) > 200:
                            content = content[:200] + "..."
                        
                        document_info += f"- **{doc.title}**: {content}\n"
            
            # Create a conversational prompt for Qwen
            conversation_prompt = f"""You are Memora, a friendly and helpful AI assistant powered by Qwen 2.5 7B, running locally on the user's computer. You have access to scheduling capabilities and can engage in natural conversation.

Key traits:
- Warm, personable, and genuinely helpful
- Knowledgeable about various topics
- Can discuss current events, answer questions, provide advice
- Remember you're also a scheduling assistant
- Keep responses concise but informative
- Use emojis naturally but not excessively

Current context: The user said "{user_message}"{document_info}

CRITICAL INSTRUCTIONS - NO HALLUCINATION:
- ONLY use information that is explicitly provided in the "RELEVANT INFORMATION FROM YOUR DOCUMENTS" section above
- If document information is provided, use ONLY that information - do not add, assume, or invent any additional details
- If NO document information is provided above, do not make up any facts about the user's certifications, achievements, or personal information
- Speak directly TO the user, not ABOUT them (use "you", "your" instead of their name in third person)
- Be conversational and personal, like you're talking to a friend
- If you see names in documents, recognize that this information belongs to the user you're talking to

WHEN ASKED ABOUT CERTIFICATIONS/ACHIEVEMENTS:
- If documents are provided above, list ONLY what is mentioned in those documents
- If NO documents are provided above, say "I don't see any certification documents uploaded yet" or similar
- NEVER make up or assume certifications that are not explicitly mentioned in the provided documents

If this seems like a scheduling request, suggest they be more specific (e.g., "To schedule something, try: 'Schedule meeting tomorrow at 3pm'").

Otherwise, respond naturally as a helpful AI assistant. You can discuss any topic, answer questions, provide explanations, give advice, or just chat friendly.

Response:"""

            try:
                model_manager = get_model_manager()
                response = model_manager.invoke(conversation_prompt)
                
                if response:
                    # Clean up the response and ensure it's helpful
                    state["response"] = response.strip()
                else:
                    # Fallback response
                    state["response"] = "🤖 I'm here to help! I can assist with scheduling tasks or just chat about anything you'd like to discuss. What's on your mind?"
                    
            except Exception as e:
                print(f"Conversation error: {e}")
                # Fallback to simple responses
                user_input = user_message.lower()
                
                if any(greeting in user_input for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
                    state["response"] = "👋 Hello! I'm Memora, your AI assistant. I can help with scheduling, answer questions, or just chat about anything you'd like. What's on your mind today?"
                
                elif any(question in user_input for question in ["what can you do", "help", "capabilities"]):
                    state["response"] = "� I'm Memora, your personal AI assistant! I can:\n\n📅 **Scheduling**: Create, view, search, and delete tasks\n� **Chat**: Discuss topics, answer questions, provide advice\n🧠 **Knowledge**: Help with explanations, problem-solving, and more\n\n💡 I'm powered by Qwen 2.5 7B running locally on your machine for privacy and speed!\n\nWhat would you like to talk about?"
                
                elif any(word in user_input for word in ["thank", "thanks", "appreciate"]):
                    state["response"] = "😊 You're very welcome! I'm always happy to help. Feel free to ask me anything - whether it's scheduling, questions, or just a friendly chat!"
                
                else:
                    state["response"] = "� I'm here to help with anything you need! I can assist with scheduling tasks, answer questions, or just have a conversation. What would you like to talk about?"
        
        elif operation == "search":
            query = state["current_task"].get("query", "")
            if query:
                tasks = task_manager.search_tasks(query)
                if tasks:
                    task_list = []
                    for task in tasks:
                        time_info = f" at {task.start_time}" if task.start_time else ""
                        status_emoji = "✅" if task.status == "completed" else "📋"
                        task_list.append(f"{status_emoji} {task.title} ({task.date}{time_info})")
                    
                    state["response"] = f"🔍 Found {len(tasks)} tasks matching '{query}':\n" + "\n".join(task_list)
                else:
                    state["response"] = f"🔍 No tasks found matching '{query}'"
            else:
                state["response"] = "❌ Please provide a search query"
        
        elif operation == "delete":
            task_id = state["current_task"].get("task_id")
            query = state["current_task"].get("query", "")
            
            if task_id:
                # Direct deletion by ID
                success = task_manager.delete_task(task_id)
                state["response"] = "✅ Task deleted successfully" if success else "❌ Failed to delete task"
            elif query:
                # Search and delete by query
                matching_tasks = task_manager.search_tasks(query)
                if matching_tasks:
                    if len(matching_tasks) == 1:
                        # Delete the single matching task
                        success = task_manager.delete_task(matching_tasks[0].id)
                        state["response"] = f"✅ Deleted task: '{matching_tasks[0].title}'" if success else "❌ Failed to delete task"
                    else:
                        # Multiple matches - show options
                        task_list = []
                        for i, task in enumerate(matching_tasks[:5], 1):
                            time_info = f" at {task.start_time}" if task.start_time else ""
                            task_list.append(f"{i}. {task.title} ({task.date}{time_info})")
                        
                        state["response"] = f"🔍 Found {len(matching_tasks)} tasks matching '{query}':\n" + "\n".join(task_list) + "\n\nPlease be more specific about which task to delete."
                else:
                    state["response"] = f"❌ No tasks found matching '{query}'"
            else:
                state["response"] = "❌ Please specify which task to delete (e.g., 'delete meeting task')"
        
        elif operation == "delete_selective":
            target_date = state["current_task"].get("date")
            task_type = state["current_task"].get("task_type", "")
            
            if target_date and task_type:
                # Get all tasks for the date
                all_tasks = task_manager.get_tasks_by_date(target_date)
                date_name = "today" if target_date == date.today().isoformat() else "tomorrow" if target_date == (date.today() + timedelta(days=1)).isoformat() else target_date
                
                # Filter tasks by type (meeting, appointment, etc.)
                tasks_to_delete = []
                for task in all_tasks:
                    task_title_lower = task.title.lower()
                    if task_type.lower() in task_title_lower:
                        tasks_to_delete.append(task)
                
                if tasks_to_delete:
                    # Get task titles before deletion
                    task_titles = [task.title for task in tasks_to_delete]
                    
                    # Delete the filtered tasks
                    deleted_count = 0
                    for task in tasks_to_delete:
                        if task_manager.delete_task(task.id):
                            deleted_count += 1
                    
                    if deleted_count > 0:
                        task_list = "\n• ".join(task_titles)
                        state["response"] = f"✅ Deleted {deleted_count} {task_type}{'s' if deleted_count > 1 else ''} for {date_name}:\n• {task_list}"
                    else:
                        state["response"] = f"❌ Failed to delete {task_type}s for {date_name}"
                else:
                    state["response"] = f"📅 No {task_type}s found for {date_name} to delete"
            else:
                state["response"] = "❌ Please specify a date and task type"
        
        elif operation == "delete_date":
            target_date = state["current_task"].get("date")
            if target_date:
                # Get tasks before deletion to show what was deleted
                tasks_to_delete = task_manager.get_tasks_by_date(target_date)
                date_name = "today" if target_date == date.today().isoformat() else "tomorrow" if target_date == (date.today() + timedelta(days=1)).isoformat() else target_date
                
                if tasks_to_delete:
                    # Get task titles before deletion
                    task_titles = [task.title for task in tasks_to_delete]
                    
                    # Delete all tasks for that date
                    deleted_count = task_manager.delete_tasks_by_date(target_date)
                    
                    if deleted_count > 0:
                        task_list = ", ".join(task_titles)
                        state["response"] = f"✅ Deleted {deleted_count} task{'s' if deleted_count > 1 else ''} for {date_name}:\n• {task_list.replace(', ', '\n• ')}"
                    else:
                        state["response"] = f"❌ Failed to delete tasks for {date_name}"
                else:
                    state["response"] = f"📅 No tasks found for {date_name} to delete"
            else:
                state["response"] = "❌ Please specify a date"
        
        elif operation == "delete_all":
            # Delete ALL tasks across all dates
            all_tasks = task_manager.get_all_tasks()
            
            if all_tasks:
                # Get task count and summary before deletion
                task_count = len(all_tasks)
                
                # Group tasks by date for summary
                tasks_by_date = {}
                for task in all_tasks:
                    date_key = task.date
                    if date_key not in tasks_by_date:
                        tasks_by_date[date_key] = []
                    tasks_by_date[date_key].append(task.title)
                
                # Delete all tasks
                deleted_count = 0
                for task in all_tasks:
                    if task_manager.delete_task(task.id):
                        deleted_count += 1
                
                if deleted_count > 0:
                    # Create summary of deleted tasks
                    date_summaries = []
                    for date_key, titles in tasks_by_date.items():
                        date_name = "today" if date_key == date.today().isoformat() else "tomorrow" if date_key == (date.today() + timedelta(days=1)).isoformat() else date_key
                        date_summaries.append(f"📅 {date_name}: {len(titles)} task{'s' if len(titles) > 1 else ''}")
                    
                    summary = "\n".join(date_summaries)
                    state["response"] = f"✅ **Deleted all {deleted_count} tasks!**\n\n{summary}\n\n🎉 Your schedule is now completely clear!"
                else:
                    state["response"] = "❌ Failed to delete tasks"
            else:
                state["response"] = "📅 No tasks found to delete. Your schedule is already clear!"
        
        elif operation == "move":
            task_data = state["task_data"]
            task_date = task_data.get("date", date.today().isoformat())
            old_time = task_data.get("old_time")
            new_time = task_data.get("new_time")
            title_hint = task_data.get("title_hint", "")
            
            # If we have title hint but no specific old_time, try to find the task by title and infer times
            if title_hint and not old_time:
                matching_tasks = task_manager.search_tasks(title_hint)
                # Filter by date if specified
                if task_date:
                    matching_tasks = [task for task in matching_tasks if task.date == task_date]
                
                if matching_tasks:
                    if len(matching_tasks) == 1:
                        task_to_move = matching_tasks[0]
                        old_time = task_to_move.start_time
                    else:
                        # Multiple matches on that date - need to be more specific
                        task_list = []
                        for task in matching_tasks[:3]:
                            time_info = f" at {task.start_time}" if task.start_time else ""
                            task_list.append(f"• {task.title} ({task.date}{time_info})")
                        
                        state["response"] = f"🔍 Found {len(matching_tasks)} tasks matching '{title_hint}':\n" + "\n".join(task_list) + "\n\nPlease be more specific about which task to reschedule."
                        return state
            
            if old_time and new_time:
                # Find the task to move
                task_to_move = task_manager.find_task_to_move(task_date, old_time, title_hint)
                
                if task_to_move:
                    # Check for conflicts with the new time (on the same date as the original task)
                    move_date = task_to_move.date  # Keep task on its original date
                    conflicting_tasks = task_manager.check_time_conflict(move_date, new_time, exclude_task_id=task_to_move.id)
                    
                    if conflicting_tasks:
                        conflict_info = []
                        for task in conflicting_tasks:
                            conflict_info.append(f"• {task.title}")
                        conflict_list = "\n".join(conflict_info)
                        date_name = "today" if move_date == date.today().isoformat() else "tomorrow" if move_date == (date.today() + timedelta(days=1)).isoformat() else "day after tomorrow" if move_date == "2025-09-16" else move_date
                        
                        state["response"] = f"⚠️ **Time Conflict!**\n\nCan't move '{task_to_move.title}' to {new_time} because there's already:\n{conflict_list}\n\n🤔 **Options:**\n1️⃣ Choose a different time\n2️⃣ Replace the existing task\n3️⃣ Move the existing task first\n\nWhat would you like to do?"
                    else:
                        # Move the task
                        success = task_manager.update_task(task_to_move.id, {"start_time": new_time})
                        if success:
                            date_name = "today" if task_to_move.date == date.today().isoformat() else "tomorrow" if task_to_move.date == (date.today() + timedelta(days=1)).isoformat() else "day after tomorrow" if task_to_move.date == "2025-09-16" else task_to_move.date
                            state["response"] = f"✅ Moved '{task_to_move.title}' from {old_time} to {new_time} on {date_name}"
                        else:
                            state["response"] = "❌ Failed to move task"
                else:
                    date_name = "today" if task_date == date.today().isoformat() else "tomorrow" if task_date == (date.today() + timedelta(days=1)).isoformat() else "day after tomorrow" if task_date == "2025-09-16" else task_date
                    state["response"] = f"❌ No task found at {old_time} on {date_name}" + (f" matching '{title_hint}'" if title_hint else "")
            elif title_hint and new_time:
                # Handle case where we just have title and new time (like "reschedule meeting with mila to 6pm")
                matching_tasks = task_manager.search_tasks(title_hint)
                if matching_tasks:
                    if len(matching_tasks) == 1:
                        task_to_move = matching_tasks[0]
                        # Check for conflicts
                        conflicting_tasks = task_manager.check_time_conflict(task_to_move.date, new_time, exclude_task_id=task_to_move.id)
                        
                        if conflicting_tasks:
                            conflict_info = []
                            for task in conflicting_tasks:
                                conflict_info.append(f"• {task.title}")
                            conflict_list = "\n".join(conflict_info)
                            
                            state["response"] = f"⚠️ **Time Conflict!**\n\nCan't move '{task_to_move.title}' to {new_time} because there's already:\n{conflict_list}\n\n🤔 **Options:**\n1️⃣ Choose a different time\n2️⃣ Replace the existing task\n3️⃣ Move the existing task first\n\nWhat would you like to do?"
                        else:
                            # Move the task
                            old_time_display = task_to_move.start_time or "unscheduled"
                            success = task_manager.update_task(task_to_move.id, {"start_time": new_time})
                            if success:
                                date_name = "today" if task_to_move.date == date.today().isoformat() else "tomorrow" if task_to_move.date == (date.today() + timedelta(days=1)).isoformat() else "day after tomorrow" if task_to_move.date == "2025-09-16" else task_to_move.date
                                state["response"] = f"✅ Moved '{task_to_move.title}' to {new_time} on {date_name}"
                            else:
                                state["response"] = "❌ Failed to move task"
                    else:
                        # Multiple matches - need to be more specific
                        task_list = []
                        for task in matching_tasks[:3]:
                            time_info = f" at {task.start_time}" if task.start_time else ""
                            date_name = "today" if task.date == date.today().isoformat() else "tomorrow" if task.date == (date.today() + timedelta(days=1)).isoformat() else "day after tomorrow" if task.date == "2025-09-16" else task.date
                            task_list.append(f"• {task.title} ({date_name}{time_info})")
                        
                        state["response"] = f"🔍 Found {len(matching_tasks)} tasks matching '{title_hint}':\n" + "\n".join(task_list) + "\n\nPlease be more specific about which task to reschedule."
                else:
                    state["response"] = f"❌ No tasks found matching '{title_hint}'"
            else:
                state["response"] = "❌ Please specify the task and new time for moving"
        
        elif operation == "update":
            task_data = state["task_data"]
            title_hint = task_data.get("title_hint", "")
            new_date = task_data.get("new_date")
            new_time = task_data.get("new_time")
            
            if title_hint:
                # Search for tasks matching the hint
                matching_tasks = task_manager.search_tasks(title_hint)
                
                if matching_tasks:
                    if len(matching_tasks) == 1:
                        task_to_update = matching_tasks[0]
                        updates = {}
                        
                        if new_date:
                            updates["date"] = new_date
                        if new_time:
                            updates["start_time"] = new_time
                        
                        if updates:
                            # Check for conflicts if updating date/time
                            if new_date and new_time:
                                conflicting_tasks = task_manager.check_time_conflict(new_date, new_time, exclude_task_id=task_to_update.id)
                                if conflicting_tasks:
                                    conflict_info = ", ".join([task.title for task in conflicting_tasks])
                                    state["response"] = f"⚠️ **Conflict!** There's already a task at {new_time} on {new_date}: {conflict_info}\n\nPlease choose a different time or resolve the conflict first."
                                    return state
                            
                            success = task_manager.update_task(task_to_update.id, updates)
                            if success:
                                update_info = []
                                if new_date:
                                    update_info.append(f"date to {new_date}")
                                if new_time:
                                    update_info.append(f"time to {new_time}")
                                state["response"] = f"✅ Updated '{task_to_update.title}' - " + " and ".join(update_info)
                            else:
                                state["response"] = "❌ Failed to update task"
                        else:
                            state["response"] = "❌ Please specify what to update (date or time)"
                    else:
                        # Multiple matches
                        task_list = []
                        for i, task in enumerate(matching_tasks[:5], 1):
                            time_info = f" at {task.start_time}" if task.start_time else ""
                            task_list.append(f"{i}. {task.title} ({task.date}{time_info})")
                        
                        state["response"] = f"🔍 Found {len(matching_tasks)} tasks matching '{title_hint}':\n" + "\n".join(task_list) + "\n\nPlease be more specific about which task to update."
                else:
                    state["response"] = f"❌ No tasks found matching '{title_hint}'"
            else:
                state["response"] = "❌ Please specify which task to update"
        
        elif operation == "context_update":
            task_data = state["task_data"]
            new_time = task_data.get("new_time")
            new_date = task_data.get("new_date") 
            context_hint = task_data.get("context_hint", "")
            
            # Try to extract context from recent conversation
            recent_tasks_mentioned = []
            if len(state["messages"]) > 1:
                # Look through recent messages for task mentions
                for msg in state["messages"][-5:]:  # Last 5 messages
                    content = msg['content'].lower()
                    if 'meeting with mila' in content:
                        recent_tasks_mentioned.append('meeting with mila')
                    elif 'doctor appointment' in content:
                        recent_tasks_mentioned.append('doctor')
                    elif 'saloon' in content:
                        recent_tasks_mentioned.append('saloon')
            
            # Try to find the task from context
            target_task = None
            if context_hint:
                matching_tasks = task_manager.search_tasks(context_hint)
                if matching_tasks:
                    target_task = matching_tasks[0]  # Take first match
            elif recent_tasks_mentioned:
                # Try the most recently mentioned task
                for hint in reversed(recent_tasks_mentioned):
                    matching_tasks = task_manager.search_tasks(hint)
                    if matching_tasks:
                        target_task = matching_tasks[0]
                        break
            
            if target_task:
                updates = {}
                if new_time:
                    # Check for conflicts at the new time
                    task_date = new_date or target_task.date
                    conflicting_tasks = task_manager.check_time_conflict(task_date, new_time, exclude_task_id=target_task.id)
                    
                    if conflicting_tasks:
                        conflict_info = ", ".join([task.title for task in conflicting_tasks])
                        state["response"] = f"⚠️ **Time Conflict!** There's already a task at {new_time}: {conflict_info}\n\nPlease choose a different time."
                        return state
                    
                    updates["start_time"] = new_time
                if new_date:
                    updates["date"] = new_date
                
                if updates:
                    success = task_manager.update_task(target_task.id, updates)
                    if success:
                        update_info = []
                        if new_time:
                            update_info.append(f"time to {new_time}")
                        if new_date:
                            update_info.append(f"date to {new_date}")
                        state["response"] = f"✅ Updated '{target_task.title}' - " + " and ".join(update_info)
                    else:
                        state["response"] = "❌ Failed to update task"
                else:
                    state["response"] = "❌ Please specify what to update (time or date)"
            else:
                state["response"] = "❌ I couldn't understand which task you're referring to. Please be more specific."
        
        elif operation == "replace":
            task_data = state["task_data"]
            old_title = task_data.get("old_title", "")
            new_title = task_data.get("new_title", "")
            task_date = task_data.get("date", date.today().isoformat())
            task_time = task_data.get("time")
            
            if old_title and new_title:
                # Find tasks to replace
                if task_time:
                    # Look for specific task at that time
                    date_tasks = task_manager.get_tasks_by_date(task_date)
                    tasks_to_replace = [task for task in date_tasks if task.start_time == task_time and old_title.lower() in task.title.lower()]
                else:
                    # Search by title only
                    tasks_to_replace = task_manager.search_tasks(old_title)
                
                if tasks_to_replace:
                    if len(tasks_to_replace) == 1:
                        task_to_replace = tasks_to_replace[0]
                        
                        # Update the task with new title
                        success = task_manager.update_task(task_to_replace.id, {"title": new_title})
                        if success:
                            time_info = f" at {task_to_replace.start_time}" if task_to_replace.start_time else ""
                            state["response"] = f"✅ Replaced '{old_title}' with '{new_title}' on {task_to_replace.date}{time_info}"
                        else:
                            state["response"] = "❌ Failed to replace task"
                    else:
                        # Multiple matches
                        task_list = []
                        for i, task in enumerate(tasks_to_replace[:3], 1):
                            time_info = f" at {task.start_time}" if task.start_time else ""
                            task_list.append(f"{i}. {task.title} ({task.date}{time_info})")
                        
                        state["response"] = f"🔍 Found {len(tasks_to_replace)} tasks matching '{old_title}':\n" + "\n".join(task_list) + "\n\nPlease be more specific about which task to replace."
                else:
                    state["response"] = f"❌ No tasks found matching '{old_title}'"
            else:
                state["response"] = "❌ Please specify both the old task and new task title"
        
        elif operation == "postpone":
            task_data = state["task_data"]
            from_date = task_data.get("from_date")
            to_date = task_data.get("to_date")
            
            if from_date and to_date:
                # Get tasks to be moved for preview
                tasks_to_move = task_manager.get_tasks_by_date(from_date)
                
                if tasks_to_move:
                    # Check for potential conflicts on target date
                    target_tasks = task_manager.get_tasks_by_date(to_date)
                    target_times = {task.start_time for task in target_tasks if task.start_time}
                    
                    conflicts = []
                    for task in tasks_to_move:
                        if task.start_time and task.start_time in target_times:
                            conflicts.append(f"• {task.title} at {task.start_time}")
                    
                    # Show conflicts if any
                    conflict_warning = ""
                    if conflicts:
                        conflict_warning = f"\n\n⚠️ **Potential conflicts on {to_date}:**\n" + "\n".join(conflicts) + "\n(Tasks will still be moved, but you may need to reschedule conflicting times)"
                    
                    # Move all tasks
                    moved_count = task_manager.postpone_tasks_by_date(from_date, to_date)
                    
                    if moved_count > 0:
                        from_name = "today" if from_date == date.today().isoformat() else "tomorrow" if from_date == (date.today() + timedelta(days=1)).isoformat() else from_date
                        to_name = "tomorrow" if to_date == (date.today() + timedelta(days=1)).isoformat() else "day after tomorrow" if to_date == (date.today() + timedelta(days=2)).isoformat() else to_date
                        
                        task_list = []
                        for task in tasks_to_move:
                            time_info = f" at {task.start_time}" if task.start_time else ""
                            task_list.append(f"• {task.title}{time_info}")
                        
                        tasks_summary = "\n".join(task_list)
                        state["response"] = f"✅ **Postponed {moved_count} task{'s' if moved_count > 1 else ''} from {from_name} to {to_name}:**\n\n{tasks_summary}{conflict_warning}"
                    else:
                        state["response"] = "❌ Failed to postpone tasks"
                else:
                    from_name = "today" if from_date == date.today().isoformat() else "tomorrow" if from_date == (date.today() + timedelta(days=1)).isoformat() else from_date
                    state["response"] = f"📅 No tasks found for {from_name} to postpone"
            else:
                state["response"] = "❌ Please specify both the source date and target date"
        
        else:
            # Default: show today's tasks
            today_tasks = task_manager.get_today_tasks()
            stats = task_manager.get_stats()
            
            if today_tasks:
                task_list = []
                for task in today_tasks:
                    time_info = f" at {task.start_time}" if task.start_time else ""
                    status_emoji = "✅" if task.status == "completed" else "📋"
                    task_list.append(f"{status_emoji} {task.title}{time_info}")
                
                state["response"] = f"📅 Today's tasks ({len(today_tasks)}):\n" + "\n".join(task_list)
            else:
                state["response"] = f"📅 No tasks for today. Total tasks: {stats['total']}"
        
    except Exception as e:
        state["error"] = str(e)
        state["response"] = f"❌ Error executing operation: {e}"
    
    return state


def response_node(state: AgentState) -> AgentState:
    """Generate final response with optional document context"""
    if state.get("error"):
        state["response"] = f"❌ I encountered an error: {state['error']}\n\nTry asking me to:\n• Create a task: 'Schedule meeting tomorrow at 3pm'\n• List tasks: 'Show my tasks'\n• Search tasks: 'Find doctor appointments'"
    
    # Enhance response with document context if available (but not for chat operations that already include it)
    try:
        if state.get("document_context") and state.get("task_operation") != "chat":
            doc_enhancement = get_document_enhancement()
            enhanced_response = doc_enhancement.enhance_response(
                state["response"], 
                state["document_context"]
            )
            state["response"] = enhanced_response
    except Exception as e:
        # Don't let document enhancement errors affect the core response
        print(f"Document enhancement error (non-critical): {e}")
    
    # Add response to messages
    state["messages"].append({
        "role": "assistant",
        "content": state["response"]
    })
    
    return state


def create_scheduling_agent():
    """Create the LangGraph scheduling agent"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("llm_analysis", llm_node)
    workflow.add_node("task_operations", task_operations_node)
    workflow.add_node("generate_response", response_node)
    
    # Add edges
    workflow.add_edge(START, "llm_analysis")
    workflow.add_edge("llm_analysis", "task_operations")
    workflow.add_edge("task_operations", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()