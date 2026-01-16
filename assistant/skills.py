import json
import re
import requests
from datetime import datetime, timedelta
from typing import List, Optional
from config.settings import Settings
from assistant.calendar import CalendarService
class Skills:
    def __init__(self):
        self.reminders_file = "reminders.json"
        self._load_dotenv()
        self.calendar_service = None
    
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
        return None
    def _get_calendar(self):
        """Lazy initialization of calendar service."""
        if self.calendar_service is None:
            try:
                self.calendar_service = CalendarService()
            except Exception as e:
                print(f"Calendar initialization failed: {e}")
                return None
        return self.calendar_service
    
    
    def get_calendar_events(self, count: int = 5) -> str:
        """Get upcoming calendar events."""
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
        """Add an event to calendar. If no time specified, uses tomorrow 10 AM."""
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
            return "Please specify a city. Example: 'weather in London'"
        
        api_key = self._get_api_key("weather", "WEATHER_API_KEY")
        if not api_key:
            return "Weather API key not configured in .env file."
        
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
                'pageSize': 5,
                'country': 'us'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok' or data.get('totalResults', 0) == 0:
                return f"No {clean_category} news articles found."
            
            headlines = f"Top {clean_category} news:\n"
            for i, article in enumerate(data['articles'][:3], 1):
                title = article.get('title', 'No title').split(' - ')[0]
                headlines += f"{i}. {title}\n"
            return headlines.strip()
            
        except requests.exceptions.RequestException as e:
            return f"Network error: {str(e)}"
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
    
    def set_reminder(self, reminder_text: str, minutes: int = 10) -> str:
        if minutes <= 0:
            return "Reminder time must be in the future."
        
        reminder_time = datetime.now() + timedelta(minutes=minutes)
        
        try:
            with open(self.reminders_file, "r") as f:
                reminders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            reminders = []
        
        reminders.append({
            "text": reminder_text,
            "time": reminder_time.isoformat(),
            "created": datetime.now().isoformat()
        })
        
        with open(self.reminders_file, "w") as f:
            json.dump(reminders, f, indent=2)
        
        return f"Reminder set for {minutes} minute(s) from now: '{reminder_text}'"
    
    def check_reminders(self) -> List[str]:
        try:
            with open(self.reminders_file, "r") as f:
                reminders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        current_time = datetime.now()
        due_reminders = []
        remaining_reminders = []
        
        for reminder in reminders:
            try:
                reminder_time = datetime.fromisoformat(reminder.get("time", ""))
                if reminder_time <= current_time:
                    due_reminders.append(reminder.get("text", "Unknown reminder"))
                else:
                    remaining_reminders.append(reminder)
            except (ValueError, KeyError):
                continue
        
        with open(self.reminders_file, "w") as f:
            json.dump(remaining_reminders, f, indent=2)
        
        return due_reminders