from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location.
    
    Args:
        location: City name or location string
    
    Examples:
        - "London" -> Weather information for London
        - "New York" -> Weather information for New York
    """
    # TODO: Integrate with real weather API (OpenWeatherMap, etc.)
    return f"Weather in {location}: Sunny, 72°F (placeholder - integrate real API)"
