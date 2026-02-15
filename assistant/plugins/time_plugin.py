from assistant.plugin_base import AssistantPlugin

class TimePlugin(AssistantPlugin):
    def get_name(self):
        return "get_current_time"
    
    def get_description(self):
        return "Get the current time and date"
    
    def get_parameters(self):
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def execute(self):
        from datetime import datetime
        now = datetime.now()
        return now.strftime("It's %I:%M %p on %A, %B %d, %Y")