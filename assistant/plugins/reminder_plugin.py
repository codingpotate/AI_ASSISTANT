from assistant.plugin_base import AssistantPlugin
from datetime import datetime
import re

class ReminderPlugin(AssistantPlugin):
    def __init__(self, database=None, session_id=None):
        self.database = database
        self.session_id = session_id

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
        if not self.database:
            return "Reminder system not available."

        try:
            reminder_time = self._parse_time_string(when)
            if reminder_time <= datetime.now():
                return "Reminder time must be in the future."

            self.database.save_reminder(
                session_id=self.session_id,
                reminder_text=reminder_text,
                due_time=reminder_time
            )
            time_str = reminder_time.strftime("%A, %B %d at %I:%M %p")
            return f"Reminder set for {time_str}: '{reminder_text}'"
        except Exception as e:
            return f"Error setting reminder: {str(e)}"

    def _parse_time_string(self, time_str: str):
        from datetime import datetime, timedelta
        time_str = time_str.lower().strip()
        now = datetime.now()

        try:
            from dateparser import parse
            parsed = parse(time_str, settings={'RELATIVE_BASE': now})
            if parsed:
                return parsed
        except ImportError:
            pass
        except Exception:
            pass

        patterns = [
            (r'in\s+(\d+)\s+minutes?', 'minutes'),
            (r'in\s+(\d+)\s+hours?', 'hours'),
            (r'in\s+(\d+)\s+days?', 'days'),
            (r'in\s+(\d+)\s+weeks?', 'weeks'),
            (r'after\s+(\d+)\s+minutes?', 'minutes'),
            (r'after\s+(\d+)\s+hours?', 'hours'),
            (r'after\s+(\d+)\s+days?', 'days'),
            (r'(\d+)\s+minutes?\s+(?:from\s+now|later)', 'minutes'),
            (r'(\d+)\s+hours?\s+(?:from\s+now|later)', 'hours'),
            (r'(\d+)\s+days?\s+(?:from\s+now|later)', 'days'),
            (r'^(\d+)\s+minutes?$', 'minutes'),
            (r'^(\d+)\s+hours?$', 'hours'),
            (r'^(\d+)\s+days?$', 'days'),
        ]

        for pattern, pattern_type in patterns:
            match = re.search(pattern, time_str)
            if match:
                value = int(match.group(1))
                if pattern_type == 'minutes':
                    return now + timedelta(minutes=value)
                elif pattern_type == 'hours':
                    return now + timedelta(hours=value)
                elif pattern_type == 'days':
                    return now + timedelta(days=value)
                elif pattern_type == 'weeks':
                    return now + timedelta(weeks=value)

        time_patterns = [
            (r'(\d+)(?::(\d+))?\s*(am|pm)', '12hr'),
            (r'at\s+(\d+)(?::(\d+))?\s*(am|pm)', '12hr'),
            (r'(\d+):(\d+)', '24hr'),
            (r'at\s+(\d+):(\d+)', '24hr'),
        ]

        for pattern, pattern_type in time_patterns:
            match = re.search(pattern, time_str)
            if match:
                if pattern_type == '12hr':
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    am_pm = match.group(3)

                    if am_pm == 'pm' and hour != 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0

                    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target_time <= now:
                        target_time += timedelta(days=1)
                    return target_time

                elif pattern_type == '24hr':
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target_time <= now:
                        target_time += timedelta(days=1)
                    return target_time

        tomorrow_match = re.search(r'tomorrow\s+(?:at\s+)?(\d+)(?::(\d+))?\s*(am|pm)?', time_str)
        if tomorrow_match:
            hour = int(tomorrow_match.group(1))
            minute = int(tomorrow_match.group(2)) if tomorrow_match.group(2) else 0
            am_pm = tomorrow_match.group(3)

            if am_pm:
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0

            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return now + timedelta(minutes=10)


class CheckRemindersPlugin(AssistantPlugin):
    def __init__(self, database=None, session_id=None):
        self.database = database
        self.session_id = session_id

    def get_name(self):
        return "check_reminders"

    def get_description(self):
        return "Check all pending and overdue reminders"

    def get_parameters(self):
        return {"type": "object", "properties": {}}

    def execute(self):
        if not self.database:
            return "Reminder system not available."

        try:
            overdue = self.database.get_due_reminders(self.session_id)
            pending = self._get_pending_reminders()

            if not overdue and not pending:
                return "No reminders found."

            result = ""
            if overdue:
                result += "Overdue reminders:\n"
                for i, reminder in enumerate(overdue, 1):
                    due_time = self._parse_db_time(reminder.get('due_time'))
                    time_str = due_time.strftime("%I:%M %p") if due_time else "unknown time"
                    result += f"{i}. {reminder.get('reminder_text', 'Unknown')} (was due at {time_str})\n"

                for reminder in overdue:
                    if 'id' in reminder:
                        self.database.mark_reminder_completed(reminder['id'])

            if pending:
                if result:
                    result += "\n"
                result += "Upcoming reminders:\n"
                for i, reminder in enumerate(pending, 1):
                    due_time = self._parse_db_time(reminder.get('due_time'))
                    if due_time:
                        time_str = due_time.strftime("%A at %I:%M %p")
                        result += f"{i}. {reminder.get('reminder_text', 'Unknown')} (due {time_str})\n"
                    else:
                        result += f"{i}. {reminder.get('reminder_text', 'Unknown')}\n"

            return result.strip()
        except Exception as e:
            return f"Error checking reminders: {str(e)}"

    def _get_pending_reminders(self):
        try:
            if hasattr(self.database, 'get_pending_reminders'):
                return self.database.get_pending_reminders(self.session_id)
            else:
                all_reminders = self.database.get_all_reminders(self.session_id)
                pending = []
                for reminder in all_reminders:
                    if reminder.get('completed', 1) == 0:
                        due_time = self._parse_db_time(reminder.get('due_time'))
                        if due_time and due_time > datetime.now():
                            pending.append(reminder)
                return pending
        except:
            return []

    def _parse_db_time(self, time_str):
        if not time_str:
            return None
        try:
            if ' ' in time_str and 'T' not in time_str:
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            if 'Z' in time_str:
                time_str = time_str.replace('Z', '+00:00')
            return datetime.fromisoformat(time_str)
        except ValueError:
            return None