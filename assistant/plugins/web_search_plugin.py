import requests
from assistant.plugin_base import AssistantPlugin

class WebSearchPlugin(AssistantPlugin):
    def get_name(self):
        return "web_search"

    def get_description(self):
        return "Search the web for information using DuckDuckGo"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str):
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            abstract = data.get('AbstractText', '')
            source = data.get('AbstractSource', '')
            url = data.get('AbstractURL', '')

            if abstract:
                result = f"{abstract}\nSource: {source}\n{url}"
            else:
                # Fallback to related topics
                topics = data.get('RelatedTopics', [])
                if topics:
                    lines = ["Related topics:"]
                    for topic in topics[:3]:
                        if isinstance(topic, dict):
                            text = topic.get('Text', '')
                            if text:
                                lines.append(f"• {text}")
                    result = "\n".join(lines) if len(lines) > 1 else "No results found."
                else:
                    result = "No results found."

            return result.strip()

        except requests.exceptions.RequestException as e:
            return f"Search request failed: {str(e)}"
        except Exception as e:
            return f"Error processing search: {str(e)}"