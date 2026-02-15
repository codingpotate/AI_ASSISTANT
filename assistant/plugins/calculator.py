from assistant.plugin_base import AssistantPlugin

class CalculatorPlugin(AssistantPlugin):
    def __init__(self, skills=None):
        self.skills = skills

    def get_name(self):
        return "calculate"

    def get_description(self):
        return "Perform basic arithmetic calculations"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression (e.g., '15 * 27 + 42')"
                }
            },
            "required": ["expression"]
        }

    def execute(self, expression: str):
        if self.skills:
            return self.skills.calculate(expression)
        return "Calculator not available."