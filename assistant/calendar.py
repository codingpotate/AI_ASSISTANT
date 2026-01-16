import os
import datetime
from typing import List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config.settings import Settings

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/calendar.events']

class CalendarService:
    """Handles authentication and core Google Calendar API interactions."""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        token_path = getattr(Settings, 'GOOGLE_TOKEN_PATH', 'token.json')
        
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=self.creds)
    
    def get_upcoming_events(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming events from the primary calendar."""
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def add_event(self, summary: str, start_time: str, end_time: str,
                  description: str = "", location: str = "") -> Dict[str, Any]:
        """Add a new event to the calendar.
        
        Args:
            summary: Event title
            start_time: ISO format string (e.g., '2024-01-20T09:00:00')
            end_time: ISO format string
            description: Optional event description
            location: Optional event location
        
        Returns:
            The created event data or error dict
        """
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            return {'success': True, 'event': event}
        except HttpError as error:
            return {'success': False, 'error': str(error)}