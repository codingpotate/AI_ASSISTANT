class LocalAI:
    
    def __init__(self):
        self.responses = {
            "greeting": [
                "Hello! I'm Jarvis, your personal assistant. How can I help you today?",
                "Hi there! What can I assist you with?",
                "Greetings! I'm here to help with various tasks."
            ],
            "farewell": [
                "Goodbye! Have a wonderful day!",
                "See you later! Feel free to return if you need anything.",
                "Take care! Don't hesitate to ask if you need assistance."
            ],
            "help": [
                "I can help with several things:\n• Check time and date\n• Get weather updates\n• Fetch news headlines\n• Perform calculations\n• Set reminders\n• And have general conversations",
                "Available commands:\n- 'What time is it?'\n- 'Weather in [city]'\n- 'Get news'\n- 'Calculate 15 * 27'\n- 'Remind me to...'\n- General conversation",
                "Try asking about:\n• Current time or date\n• Weather conditions\n• Latest news\n• Mathematical calculations\n• Or just chat with me!"
            ],
            "thanks": [
                "You're welcome! Happy to help.",
                "My pleasure! Let me know if you need anything else.",
                "Anytime! That's what I'm here for."
            ],
            "unknown": [
                "I'm not sure how to help with that. Try asking about time, weather, news, or calculations.",
                "I don't have that capability yet. Would you like help with something else?",
                "For now, I can help with basic tasks. Try asking something like 'What can you do?'"
            ]
        }
    
    def process(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return random.choice(self.responses["greeting"])
        
        if any(word in text_lower for word in ['bye', 'goodbye', 'exit', 'quit', 'see you']):
            return random.choice(self.responses["farewell"])
        
        if any(word in text_lower for word in ['help', 'what can you do', 'capabilities']):
            return random.choice(self.responses["help"])
        
        if any(word in text_lower for word in ['thanks', 'thank you', 'appreciate']):
            return random.choice(self.responses["thanks"])
        
        if 'time' in text_lower and 'date' not in text_lower:
            now = datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')}."
        
        if 'date' in text_lower:
            now = datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}."
        
        if 'weather' in text_lower:
            city_match = re.search(r'weather\s+(?:in\s+)?([a-zA-Z\s]+)', text_lower)
            city = city_match.group(1).strip() if city_match else None
            city_msg = f" in {city}" if city else ""
            return f"I can check weather{city_msg} if you add a Weather API key to the .env file."

        if 'news' in text_lower:
            return "I can fetch news if you add a NewsAPI key to the .env file."

        if 'calculate' in text_lower or re.search(r'what is \d+', text_lower):
            return "I can perform calculations if you add a WolframAlpha API key to the .env file."

        if any(word in text_lower for word in ['who are you', 'your name', 'what are you']):
            return "I'm Jarvis, your AI personal assistant. I'm here to help with various tasks and answer questions."

        if 'how are you' in text_lower:
            return random.choice([
                "I'm functioning optimally, thank you for asking!",
                "I'm doing well, ready to assist you!",
                "All systems operational! How can I help you today?"
            ])
        
        if 'remind' in text_lower or 'reminder' in text_lower:
            return "Reminder system should be handled by the main AI core. Try saying it again."
        
        return random.choice(self.responses["unknown"])