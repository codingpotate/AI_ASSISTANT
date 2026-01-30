"""
Weather plugin implementation.
"""
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from assistant.plugin_base import AssistantPlugin

load_dotenv()

class WeatherPlugin(AssistantPlugin):
    def get_name(self) -> str:
        return "get_weather"
    
    def get_description(self) -> str:
        return "Get current weather information for a specified city."
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name to get weather for, e.g., 'London' or 'New York'"
                }
            },
            "required": ["city"]
        }
    
    def execute(self, **kwargs) -> str:
        city = kwargs.get("city")
        if not city:
            return "Error: City parameter is required"
        
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key or api_key.startswith("your_weather_api_key"):
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
        except (KeyError, IndexError) as e:
            return f"Error processing weather data: {str(e)}"