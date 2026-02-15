import json
import re
import requests
import os
from datetime import datetime, timedelta
from typing import List, Optional
from config.settings import Settings
from assistant.calendar import CalendarService

class Skills:
    def __init__(self, database=None, session_id="default_session"):
        self.reminders_file = "reminders.json"
        self._load_dotenv()
        self.calendar_service = None
        self.database = database
        self.session_id = session_id
        
        if self.database:
            try:
                test = self.database.get_user_settings(self.session_id)
            except Exception as e:
                self.database = None
    
    def _load_dotenv(self):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
    
    def _get_api_key(self, key_name: str, env_var: str) -> Optional[str]:
        key = getattr(Settings, env_var, None)
        if key and not key.startswith(f"your_{key_name}_api_key"):
            return key
        return os.getenv(env_var)
    
    def _get_calendar(self):
        if self.calendar_service is None:
            try:
                self.calendar_service = CalendarService()
            except Exception as e:
                return None
        return self.calendar_service
    
    def get_calendar_events(self, count: int = 5) -> str:
        calendar = self._get_calendar()
        if not calendar:
            return "Calendar service not available. Check credentials."
        
        events = calendar.get_upcoming_events(count)
        
        if not events:
            return "No upcoming events found."
        
        response = f"Your next {len(events)} events:\n"
        for i, event in enumerate(events, 1):
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No title')
            
            try:
                if 'T' in start:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_str = dt.strftime("%a %b %d at %I:%M %p")
                else:
                    date_obj = datetime.fromisoformat(start)
                    time_str = date_obj.strftime("%a %b %d (All day)")
            except:
                time_str = start
            
            response += f"{i}. {time_str}: {summary}\n"
        
        return response.strip()
    
    def add_calendar_event(self, summary: str, start_time: str = None, 
                          duration_hours: int = 1) -> str:
        calendar = self._get_calendar()
        if not calendar:
            return "Calendar service not available. Check credentials."

        if not start_time:
            tomorrow = datetime.now() + timedelta(days=1)
            start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            start_iso = start_time.isoformat()
            end_iso = (start_time + timedelta(hours=duration_hours)).isoformat()
        else:
            start_iso = start_time
            end_time_obj = datetime.fromisoformat(start_time) + timedelta(hours=duration_hours)
            end_iso = end_time_obj.isoformat()
        
        result = calendar.add_event(
            summary=summary,
            start_time=start_iso,
            end_time=end_iso
        )
        
        if result['success']:
            event = result['event']
            return f"Event added: '{event['summary']}' on {event['start'].get('dateTime', event['start'].get('date'))}"
        else:
            return f"Failed to add event: {result.get('error', 'Unknown error')}"
    
    def get_time_date(self) -> str:
        now = datetime.now()
        return now.strftime("It's %I:%M %p on %A, %B %d, %Y")
    
    def get_weather(self, city: str = None) -> str:
        if not city or city.strip() == "":
            city = "London"
        
        api_key = self._get_api_key("weather", "WEATHER_API_KEY")
        if not api_key:
            return f"Weather API key not configured. Add WEATHER_API_KEY to .env file for real data in {city}."
        
        try:
            geo_url = "http://api.openweathermap.org/geo/1.0/direct"
            geo_params = {'q': city, 'limit': 1, 'appid': api_key}
            geo_response = requests.get(geo_url, params=geo_params, timeout=10)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            
            if not geo_data:
                return f"Could not find city '{city}'. Try a different spelling."
            
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            weather_params = {
                'lat': lat, 'lon': lon, 'appid': api_key,
                'units': 'metric', 'lang': 'en'
            }
            
            weather_response = requests.get(weather_url, params=weather_params, timeout=10)
            weather_response.raise_for_status()
            data = weather_response.json()
            
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            description = data['weather'][0]['description']
            city_name = data['name']
            country = data['sys']['country']
            
            return (f"Weather in {city_name}, {country}: {description}. "
                   f"Temperature: {temp:.1f}°C (feels like {feels_like:.1f}°C), "
                   f"Humidity: {humidity}%.")
            
        except requests.exceptions.RequestException as e:
            return f"Network error: {str(e)}"
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return f"Error processing data: {str(e)}"
    
    def get_news(self, category: str = "general") -> str:
        api_key = self._get_api_key("news", "NEWS_API_KEY")
        if not api_key:
            return "News API key not configured in .env file."
        
        valid_categories = ["general", "technology", "business", "sports", 
                        "entertainment", "health", "science"]
        clean_category = category.lower().strip()
        if clean_category not in valid_categories:
            clean_category = "general"
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'category': clean_category,
                'apiKey': api_key,
                'pageSize': 10,
                'country': 'us',
                'language': 'en'
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                return f"News API returned error: {data.get('message', 'Unknown error')}"
            
            if data.get('totalResults', 0) == 0:
                return f"No {clean_category} news articles found."
            
            articles = data['articles'][:5]
            
            articles = [a for a in articles if a.get('title') and a['title'] != '[Removed]']
            
            if not articles:
                return "No valid news articles found (some may have been removed)."
            
            headlines = f"Top {clean_category} news:\n"
            headlines += "-" * 40 + "\n"
            
            for i, article in enumerate(articles, 1):
                title = article.get('title', 'No title').split(' - ')[0]
                source = article.get('source', {}).get('name', 'Unknown')
                
                if len(title) > 80:
                    title = title[:77] + "..."
                
                headlines += f"{i}. {title}\n"
                headlines += f"   Source: {source}\n"
                
                description = article.get('description', '')
                if description and len(description) > 5 and description != title:
                    if len(description) > 100:
                        description = description[:97] + "..."
                    headlines += f"   {description}\n"
                
                headlines += "\n"
            
            return headlines.strip()
            
        except requests.exceptions.Timeout:
            return "News request timed out. Please try again later."
        except requests.exceptions.RequestException as e:
            return f"Network error while fetching news: {str(e)}"
        except (KeyError, json.JSONDecodeError) as e:
            return f"Error processing news data: {str(e)}"
    
    def calculate(self, expression: str) -> str:
        try:
            clean_expr = expression.lower().replace('calculate', '').replace('what is', '').strip()
            
            if not re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', clean_expr):
                return "I can only perform basic arithmetic calculations."
            
            result = eval(clean_expr)
            return f"{clean_expr} = {result}"
        except ZeroDivisionError:
            return "Error: Division by zero is not allowed."
        except Exception:
            return "I couldn't calculate that. Try something like '15 * 27'."
    
    def set_reminder(self, reminder_text: str, when: str = "in 10 minutes") -> str:
        try:
            reminder_time = self._parse_time_string(when)
            
            # Fix the time comparison logic
            current_time = datetime.now()
            
            # Check if reminder time is in the past
            if reminder_time < current_time:
                # Calculate how far in the past
                time_diff = current_time - reminder_time
                seconds_diff = time_diff.total_seconds()
                
                # Convert to appropriate units
                if seconds_diff < 60:
                    return f"Reminder time is {int(seconds_diff)} seconds in the past. Please specify a future time."
                elif seconds_diff < 3600:
                    minutes_diff = int(seconds_diff / 60)
                    return f"Reminder time is {minutes_diff} minutes in the past. Please specify a future time."
                else:
                    hours_diff = int(seconds_diff / 3600)
                    return f"Reminder time is {hours_diff} hours in the past. Please specify a future time."
            
            # Save reminder to database
            if self.database:
                self.database.save_reminder(
                    session_id=self.session_id,
                    reminder_text=reminder_text,
                    due_time=reminder_time
                )
                
                time_str = reminder_time.strftime("%A, %B %d at %I:%M %p")
                return f"Reminder set for {time_str}: '{reminder_text}'"
            else:
                # Fallback to file storage
                return self._save_reminder_to_file(reminder_text, reminder_time)
                
        except Exception as e:
            return f"Error setting reminder: {str(e)}"
    def _parse_time_string(self, time_str: str) -> datetime:
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
                        target_time = target_time + timedelta(days=1)
                    
                    return target_time
                
                elif pattern_type == '24hr':
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    
                    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    if target_time <= now:
                        target_time = target_time + timedelta(days=1)
                    
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
    
    def _save_reminder_to_file(self, reminder_text: str, due_time: datetime) -> str:
        try:
            reminders = []
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r') as f:
                    reminders = json.load(f)
            
            reminders.append({
                "text": reminder_text,
                "due_time": due_time.isoformat(),
                "created": datetime.now().isoformat()
            })
            
            with open(self.reminders_file, 'w') as f:
                json.dump(reminders, f, indent=2)
            
            time_str = due_time.strftime("%A, %B %d at %I:%M %p")
            return f"Reminder set for {time_str}: '{reminder_text}' (saved to file)"
        except Exception as e:
            return f"Error saving reminder to file: {str(e)}"
    
    def check_reminders(self) -> str:
        try:
            if self.database:
                overdue = self.database.get_due_reminders(self.session_id)
                
                pending = self._get_pending_reminders_from_db()
                
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
            else:
                return self._check_file_reminders()
                
        except Exception as e:
            return f"Error checking reminders: {str(e)}"
    
    def _get_pending_reminders_from_db(self):
        try:
            if hasattr(self.database, 'get_pending_reminders'):
                return self.database.get_pending_reminders(self.session_id)
            else:
                try:
                    all_reminders = self.database.get_all_reminders(self.session_id)
                except AttributeError:
                    return []
                
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
            # Handle SQLite format (YYYY-MM-DD HH:MM:SS)
            if ' ' in time_str and 'T' not in time_str:
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            
            # Handle ISO format (with or without timezone)
            if 'Z' in time_str:
                time_str = time_str.replace('Z', '+00:00')
            
            return datetime.fromisoformat(time_str)
            
        except ValueError:
            return None
    
    def _check_file_reminders(self) -> str:
        try:
            if not os.path.exists(self.reminders_file):
                return "No reminders file found."
            
            with open(self.reminders_file, 'r') as f:
                reminders = json.load(f)
            
            current_time = datetime.now()
            due_reminders = []
            pending_reminders = []
            remaining_reminders = []
            
            for reminder in reminders:
                try:
                    due_time = datetime.fromisoformat(reminder.get("due_time", ""))
                    if due_time <= current_time:
                        due_reminders.append(reminder.get("text", "Unknown reminder"))
                    else:
                        pending_reminders.append(reminder)
                        remaining_reminders.append(reminder)
                except (ValueError, KeyError):
                    continue
            
            with open(self.reminders_file, 'w') as f:
                json.dump(remaining_reminders, f, indent=2)
            
            if not due_reminders and not pending_reminders:
                return "No reminders found."
            
            result = ""
            if due_reminders:
                result += "Due reminders:\n"
                for i, text in enumerate(due_reminders, 1):
                    result += f"{i}. {text}\n"
            
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
            return f"Error checking file reminders: {str(e)}"
    
    def clear_reminders(self) -> str:
        try:
            if self.database:
                return "Reminder clearing for database not implemented yet."
            else:
                if os.path.exists(self.reminders_file):
                    os.remove(self.reminders_file)
                    return "All reminders cleared."
                else:
                    return "No reminders file found."
        except Exception as e:
            return f"Error clearing reminders: {str(e)}"