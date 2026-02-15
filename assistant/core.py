import json
import os
import hashlib
import getpass
from datetime import datetime
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
        check_keywords = ['check', 'what', 'show', 'list', 'get']
        set_keywords = ['set', 'create', 'add', 'make']
        
        has_reminder_word = any(word in text_lower for word in reminder_keywords)
        
        if not has_reminder_word:
            return None
        
        if not self.skills:
            return "Reminder system not available. Skills module not loaded."
        
        has_check_word = any(word in text_lower for word in check_keywords)
        
        if has_check_word:
            return self.skills.check_reminders()
        
        # Parse reminder text and time
        import re
        
        # Clean common patterns
        cleaned_text = text_lower
        
        # Remove common prefixes
        prefixes = ['remind me to', 'set reminder for', 'create reminder for', 
                    'remind me', 'set reminder', 'create reminder', 'add reminder']
        
        for prefix in prefixes:
            if cleaned_text.startswith(prefix):
                cleaned_text = cleaned_text[len(prefix):].strip()
                break
        
        if cleaned_text.startswith('to '):
            cleaned_text = cleaned_text[3:].strip()
        

        time_patterns = [
            r'(?:in|at|on|for)\s+(.+)',  # "in 2 hours", "at 4pm", "on monday"
            r'(.+?)\s+(?:in|at|on|for)\s+(.+)',  # "call mom in 2 hours"
        ]
        
        reminder_text = ""
        when = ""
        
        for pattern in time_patterns:
            match = re.search(pattern, cleaned_text)
            if match:
                if len(match.groups()) == 1:
                    when = match.group(1).strip()
                    time_expr = match.group(0)
                    reminder_text = cleaned_text.replace(time_expr, '').strip()
                else:
                    reminder_text = match.group(1).strip()
                    when = match.group(2).strip()
                break
        
        if not when:
            duration_pattern = r'(\d+\s+(?:minutes?|hours?|days?|weeks?))'
            match = re.search(duration_pattern, cleaned_text)
            if match:
                when = match.group(0).strip()
                reminder_text = cleaned_text.replace(when, '').strip()
        
        if reminder_text:
            reminder_text = re.sub(r'\s+(?:to|for)$', '', reminder_text)
        
        if reminder_text and when:
            if re.match(r'\d+\s+(?:minutes?|hours?|days?|weeks?)', when) and not when.startswith('in '):
                when = 'in ' + when
            
            return self.skills.set_reminder(reminder_text, when)
        
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
        # Get FRESH system prompt with current time EVERY TIME
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
        from assistant.local_ai import LocalAI
        
        reminder_response = self._process_reminder_directly(text)
        if reminder_response:
            return reminder_response
        
        local_ai = LocalAI()
        return local_ai.process(text)
    
    def get_available_skills(self) -> List[str]:
        if self.plugin_registry:
            return [plugin.get_name() for plugin in self.plugin_registry.get_all_plugins()]
        return []
    
    def get_session_stats(self) -> Dict[str, Any]:
        history = self.database.get_conversation_history(self.session_id)
        
        user_messages = [msg for msg in history if msg["role"] == "user"]
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
        
        return {
            "session_id": self.session_id,
            "total_messages": len(history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "plugins_used": len([msg for msg in history if msg.get("plugin_used")]),
            "start_time": history[0]["created_at"] if history else None,
            "end_time": history[-1]["created_at"] if history else None
        }
    
    def clear_history(self):
        self.conversation_history = []