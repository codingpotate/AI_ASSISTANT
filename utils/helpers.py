"""
Helper functions
"""

def extract_city(text: str) -> str:
    """Extract city name from text"""
    import re
    patterns = [
        r'weather\s+in\s+([a-zA-Z\s]+)',
        r'weather\s+for\s+([a-zA-Z\s]+)',
        r'in\s+([a-zA-Z\s]+)\s+weather'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

def format_response(text: str, max_length: int = 200) -> str:
    """Format response text"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text