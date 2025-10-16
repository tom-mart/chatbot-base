from langchain_core.tools import tool
from datetime import datetime
from zoneinfo import ZoneInfo

@tool
def get_current_time() -> str:
    """Get the EXACT current date and time right now. 
    
    Use this tool whenever the user asks about the current time, date, or "what time is it".
    Returns the actual current time in ISO format (YYYY-MM-DD HH:MM:SS).
    
    DO NOT guess or explain time zones - always call this tool to get the real time.
    """
    # Get current time in local timezone (system timezone)
    # For UK/London, use 'Europe/London' which handles BST/GMT automatically
    local_tz = ZoneInfo('Europe/London')  # Change this to your timezone
    return datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
