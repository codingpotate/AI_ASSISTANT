from assistant.plugin_base import AssistantPlugin
from datetime import datetime
import json
import os

class ReminderPlugin(AssistantPlugin):
    def __init__(self):
        self.reminders_file = "reminders.json"
    
    def get_name(self):
        return "set_reminder"
    
    def get_description(self):
        return "Set a reminder for a specific time"
    
    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "reminder_text": {
                    "type": "string",
                    "description": "The reminder message"
                },
                "when": {
                    "type": "string",
                    "description": "When to remind (e.g., 'in 10 minutes', 'tomorrow at 2pm')"
                }
            },
            "required": ["reminder_text", "when"]
        }
    
    def execute(self, reminder_text: str, when: str):
        from datetime import datetime, timedelta
        import re
        
        try:
            # Parse time
            reminder_time = self._parse_time_string(when)
            
            if not reminder_time or reminder_time <= datetime.now():
                return "Reminder time must be in the future."
            
            # Save to file
            reminders = []
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r') as f:
                    reminders = json.load(f)
            
            reminders.append({
                "text": reminder_text,
                "due_time": reminder_time.isoformat(),
                "created": datetime.now().isoformat()
            })
            
            with open(self.reminders_file, 'w') as f:
                json.dump(reminders, f, indent=2)
            
            time_str = reminder_time.strftime("%A, %B %d at %I:%M %p")
            return f"Reminder set for {time_str}: '{reminder_text}'"
            
        except Exception as e:
            return f"Error setting reminder: {str(e)}"
    
    def _parse_time_string(self, time_str: str):
        from datetime import datetime, timedelta
        import re
        
        time_str = time_str.lower().strip()
        now = datetime.now()
        
        # Simple parsing
        patterns = [
            (r'in\s+(\d+)\s+minutes?', 'minutes'),
            (r'in\s+(\d+)\s+hours?', 'hours'),
            (r'in\s+(\d+)\s+days?', 'days'),
            (r'(\d+)\s+minutes?', 'minutes'),
            (r'(\d+)\s+hours?', 'hours'),
            (r'(\d+)\s+days?', 'days'),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, time_str)
            if match:
                if pattern_type == 'minutes':
                    minutes = int(match.group(1))
                    return now + timedelta(minutes=minutes)
                elif pattern_type == 'hours':
                    hours = int(match.group(1))
                    return now + timedelta(hours=hours)
                elif pattern_type == 'days':
                    days = int(match.group(1))
                    return now + timedelta(days=days)
        
        return now + timedelta(minutes=10)


class CheckRemindersPlugin(AssistantPlugin):
    def __init__(self):
        self.reminders_file = "reminders.json"
    
    def get_name(self):
        return "check_reminders"
    
    def get_description(self):
        return "Check all pending and overdue reminders"
    
    def get_parameters(self):
        return {
            "type": "object",
            "properties": {}
        }
    
    def execute(self):
        try:
            if not os.path.exists(self.reminders_file):
                return "No reminders found."
            
            with open(self.reminders_file, 'r') as f:
                reminders = json.load(f)
            
            from datetime import datetime
            current_time = datetime.now()
            
            due_reminders = []
            pending_reminders = []
            
            for reminder in reminders:
                try:
                    due_time = datetime.fromisoformat(reminder.get("due_time", ""))
                    if due_time <= current_time:
                        due_reminders.append(reminder)
                    else:
                        pending_reminders.append(reminder)
                except (ValueError, KeyError):
                    continue
            
            if not due_reminders and not pending_reminders:
                return "No reminders found."
            
            result = ""
            if due_reminders:
                result += "Due reminders:\n"
                for i, reminder in enumerate(due_reminders, 1):
                    result += f"{i}. {reminder.get('text', 'Unknown')}\n"
            
            if pending_reminders:
                if result:
                    result += "\n"
                result += "Pending reminders:\n"
                for i, reminder in enumerate(pending_reminders, 1):
                    due_time = datetime.fromisoformat(reminder.get("due_time", ""))
                    time_str = due_time.strftime("%A at %I:%M %p")
                    result += f"{i}. {reminder.get('text', 'Unknown')} (due {time_str})\n"
            
            return result.strip()
        except Exception as e:
            return f"Error checking reminders: {str(e)}"