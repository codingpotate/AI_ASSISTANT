from assistant.plugin_base import AssistantPlugin

class NewsPlugin(AssistantPlugin):
    def __init__(self, skills=None):
        self.skills = skills

    def get_name(self):
        return "get_news"

    def get_description(self):
        return "Get latest news headlines for a category"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "News category (general, technology, business, sports, entertainment, health, science)",
                    "enum": ["general", "technology", "business", "sports", "entertainment", "health", "science"]
                }
            },
            "required": []
        }

    def execute(self, category="general"):
        if self.skills:
            return self.skills.get_news(category)
        return "News system not available."