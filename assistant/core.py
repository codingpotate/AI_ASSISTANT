import json
import os
import hashlib
import getpass
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI
from config.settings import Settings
from assistant.database import Database

class AICore:
    def __init__(self, plugin_registry=None, user_identifier=None, skills=None, session_id=None):
        if session_id:
            self.session_id = session_id
        elif user_identifier:
            self.session_id = hashlib.md5(user_identifier.encode()).hexdigest()[:16]
        else:
            username = getpass.getuser()
            self.session_id = f"user_{hashlib.md5(username.encode()).hexdigest()[:8]}"

        self.conversation_history = []
        self.system_prompt = Settings.get_system_prompt()
        self._tools = []
        self.max_history_length = 20
        self.plugin_registry = plugin_registry
        self.database = Database()
        self.skills = skills

        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            self.use_gemini = False
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            self.use_gemini = True

        self._load_history_from_db()

    def _load_history_from_db(self):
        db_history = self.database.get_conversation_history(self.session_id, limit=self.max_history_length)
        for entry in db_history:
            self.conversation_history.append({
                "role": entry["role"],
                "content": entry["content"],
                "timestamp": entry["created_at"]
            })
        if db_history:
            print(f"Loaded {len(db_history)} previous messages for session: {self.session_id}")

    def process_command(self, text: str) -> str:
        self.database.save_conversation(
            session_id=self.session_id,
            role="user",
            content=text
        )
        self.conversation_history.append({"role": "user", "content": text})

        # Direct handling for reminders
        reminder_response = self._process_reminder_directly(text)
        if reminder_response:
            self.database.save_conversation(
                session_id=self.session_id,
                role="assistant",
                content=reminder_response,
                plugin_used="reminder"
            )
            self._update_history(text, reminder_response)
            return reminder_response

        # Direct handling for file organization
        text_lower = text.lower()
        if 'organize files' in text_lower or 'organize folder' in text_lower:
            match = re.search(r'organize (?:files|folder)(?:\s+in)?\s+(.+)', text_lower)
            if match:
                directory = match.group(1).strip()
                plugin = self.plugin_registry.get_plugin('organize_files')
                if plugin:
                    try:
                        response = plugin.execute(directory=directory)
                        self.database.save_conversation(
                            session_id=self.session_id,
                            role="assistant",
                            content=response,
                            plugin_used="organize_files"
                        )
                        self._update_history(text, response)
                        return response
                    except Exception as e:
                        error_msg = f"Error organizing files: {str(e)}"
                        self.database.save_conversation(
                            session_id=self.session_id,
                            role="assistant",
                            content=error_msg,
                            plugin_used="error"
                        )
                        self._update_history(text, error_msg)
                        return error_msg

        # Direct handling for calculations
        calc_keywords = ['calculate', 'what is', '=', 'multiplied', 'divided', 'plus', 'minus']
        if any(keyword in text_lower for keyword in calc_keywords) or re.search(r'\d+\s*[\+\-\*\/]\s*\d+', text_lower):
            expr = re.sub(r'(calculate|what is|equals?|=)', '', text_lower).strip()
            plugin = self.plugin_registry.get_plugin('calculate')
            if plugin:
                try:
                    response = plugin.execute(expression=expr)
                    self.database.save_conversation(
                        session_id=self.session_id,
                        role="assistant",
                        content=response,
                        plugin_used="calculate"
                    )
                    self._update_history(text, response)
                    return response
                except Exception as e:
                    error_msg = f"Error calculating: {str(e)}"
                    self.database.save_conversation(
                        session_id=self.session_id,
                        role="assistant",
                        content=error_msg,
                        plugin_used="error"
                    )
                    self._update_history(text, error_msg)
                    return error_msg

        # Try Gemini if available
        try:
            if self.use_gemini and self.client:
                return self._process_with_gemini(text)
            else:
                return self._fallback_response(text)
        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            self.database.save_conversation(
                session_id=self.session_id,
                role="assistant",
                content=error_msg,
                plugin_used="error"
            )
            self._update_history(text, error_msg)
            return error_msg
    def _process_reminder_directly(self, text: str):
        text_lower = text.lower()
        reminder_keywords = ['remind', 'reminder', 'alarm', 'notify', 'remember']
        if not any(word in text_lower for word in reminder_keywords):
            return None
        if not self.skills:
            return "Reminder system not available."

        patterns = [
            # task first, then time
            (r'remind\s+me\s+to\s+(.+?)\s+(?:at|on|in)\s+(.+)', 1, 2),
            (r'set\s+(?:a\s+)?reminder\s+for\s+(.+?)\s+(?:at|on|in)\s+(.+)', 1, 2),
            (r'remind\s+me\s+(.+?)\s+(?:at|on|in)\s+(.+)', 1, 2),
            (r'reminder\s+(.+?)\s+(?:at|on|in)\s+(.+)', 1, 2),
            # time first, then task
            (r'(?:at|on|in)\s+(.+?)\s+remind\s+me\s+to\s+(.+)', 2, 1),
            (r'(?:at|on|in)\s+(.+?)\s+set\s+(?:a\s+)?reminder\s+for\s+(.+)', 2, 1),
            (r'remind\s+me\s+(?:at|on|in)\s+(.+?)\s+to\s+(.+)', 2, 1),
            (r'remind\s+(?:at|on|in)\s+(.+?)\s+to\s+(.+)', 2, 1),
            (r'set\s+(?:a\s+)?reminder\s+(?:at|on|in)\s+(.+?)\s+for\s+(.+)', 2, 1),
            (r'(?:at|on|in)\s+(.+?)\s+(?:remind\s+me|reminder)\s+(.+)', 2, 1),
            # very generic last resort
            (r'(.+?)\s+(?:at|on|in)\s+(.+)', 1, 2),
        ]

        for pattern, task_idx, time_idx in patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                task = groups[task_idx-1].strip()
                when = groups[time_idx-1].strip()
                # Clean up task: remove leading 'to', 'a', 'the', 'my'
                task = re.sub(r'^(?:to|a|the|my)\s+', '', task)
                # If task is just 'remind' or 'reminder', skip this pattern
                if task in ['remind', 'reminder']:
                    continue
                return self.skills.set_reminder(task, when)

        # Fallback: extract any time expression
        time_pattern = r'(?:at|on|in)\s+(\d+\s*(?:minutes?|hours?|days?|weeks?|am|pm)|tomorrow|next\s+\w+|\d{1,2}(?::\d{2})?\s*(?:am|pm)?)'
        time_match = re.search(time_pattern, text_lower)
        if time_match:
            time_expr = time_match.group(0).strip()
            task = text_lower.replace(time_expr, '').strip()
            task = re.sub(r'^(remind\s+me|set\s+(?:a\s+)?reminder|reminder)\s+', '', task)
            task = re.sub(r'\s+to$', '', task)
            if task and task not in ['remind', 'reminder']:
                return self.skills.set_reminder(task, time_expr)

        return "Please specify what to remind and when. Example: 'remind me to call mom in 2 hours' or 'set reminder for meeting tomorrow at 2pm'"
    def _process_with_gemini(self, text: str) -> str:
        try:
            if not self._tools and self.plugin_registry:
                self._load_tools()
            
            messages = self._build_message_list(text)
            
            if not self._tools:
                response = self.client.chat.completions.create(
                    model="gemini-2.5-flash",
                    messages=messages,
                    max_tokens=500
                )
                final_response = response.choices[0].message.content
                plugin_used = None
            else:
                response = self.client.chat.completions.create(
                    model="gemini-2.5-flash",
                    messages=messages,
                    tools=[{"type": "function", "function": tool} for tool in self._tools],
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    plugin_used = message.tool_calls[0].function.name if message.tool_calls else None
                    tool_messages = self._handle_tool_calls(messages, message)
                    final_response = self._get_final_response(tool_messages)
                    
                    if plugin_used:
                        self.database.update_plugin_stats(plugin_used, self.session_id)
                else:
                    final_response = message.content
                    plugin_used = None
            
            self.database.save_conversation(
                session_id=self.session_id,
                role="assistant",
                content=final_response,
                plugin_used=plugin_used
            )
            
            self._update_history(text, final_response)
            return final_response
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_response(text)
    
    def _build_message_list(self, current_text: str) -> List[Dict[str, Any]]:
        from config.settings import Settings
        
        messages = []
        fresh_system_prompt = Settings.get_system_prompt()
        messages.append({"role": "system", "content": fresh_system_prompt})
        
        for entry in self.conversation_history[-self.max_history_length:]:
            if isinstance(entry, dict):
                if entry.get("role") == "user":
                    messages.append({"role": "user", "content": entry.get("content", "")})
                elif entry.get("role") == "assistant":
                    messages.append({"role": "assistant", "content": entry.get("content", "")})
        
        messages.append({"role": "user", "content": current_text})
        return messages
    
    def _handle_tool_calls(self, messages: List[Dict[str, Any]], message: Any) -> List[Dict[str, Any]]:
        messages.append({
            "role": "assistant",
            "content": message.content if message.content else "",
            "tool_calls": message.tool_calls
        })
        
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            result = self.plugin_registry.execute_plugin(function_name, **function_args) if self.plugin_registry else f"Plugin '{function_name}' not available"
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
        
        return messages
    
    def _get_final_response(self, messages: List[Dict[str, Any]]) -> str:
        second_response = self.client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=messages
        )
        return second_response.choices[0].message.content
    
    def _update_history(self, user_message: str, assistant_response: str):
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-(self.max_history_length * 2):]
    
    def _load_tools(self):
        if not self.plugin_registry:
            return
            
        self._tools = []
        for plugin in self.plugin_registry.get_all_plugins():
            metadata = plugin.get_metadata()
            self._tools.append({
                "name": metadata["name"],
                "description": metadata["description"],
                "parameters": metadata["parameters"]
            })
        
        print(f"Loaded {len(self._tools)} tools for AI")
    
    def _fallback_response(self, text: str) -> str:
        text_lower = text.lower()

        if any(word in text_lower for word in ['time', 'clock']):
            return self.skills.get_time_date()
        if 'date' in text_lower:
            return self.skills.get_time_date()

        if 'weather' in text_lower:
            city = None
            city_match = re.search(r'weather\s+(?:in\s+)?([a-zA-Z\s]+)', text_lower)
            if city_match:
                city = city_match.group(1).strip()
            return self.skills.get_weather(city)

        if 'news' in text_lower:
            category = 'general'
            category_match = re.search(r'news\s+(?:about\s+)?([a-zA-Z]+)', text_lower)
            if category_match:
                cat = category_match.group(1).strip().lower()
                valid = ['technology', 'business', 'sports', 'entertainment', 'health', 'science']
                if cat in valid:
                    category = cat
            return self.skills.get_news(category)

        if any(word in text_lower for word in ['calendar', 'events', 'schedule']):
            return self.skills.get_calendar_events()

        if any(word in text_lower for word in ['calculate', 'what is', '=']):
            expr = re.sub(r'(calculate|what is|equals?|=)', '', text_lower).strip()
            if expr:
                return self.skills.calculate(expr)

        from assistant.local_ai import LocalAI
        local = LocalAI()
        return local.process(text)
    
    def clear_history(self):
        self.conversation_history = []