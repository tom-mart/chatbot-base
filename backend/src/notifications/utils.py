"""
Utility functions for notifications, including natural language date/time parsing.
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def parse_reminder_datetime(text: str, user_timezone=None) -> Optional[datetime]:
    """
    Parse natural language date/time expressions into datetime objects.
    
    Supports:
    - Specific times: "at 3pm", "at 15:00", "at 9:30am"
    - Specific dates: "on Monday", "next Wednesday", "tomorrow", "on 2025-10-15"
    - Relative times: "in 2 hours", "in 30 minutes", "in 1 week"
    - Combined: "tomorrow at 9am", "next Monday at 3pm"
    
    Args:
        text: Natural language text containing date/time
        user_timezone: User's timezone (optional)
        
    Returns:
        datetime object or None if parsing fails
    """
    from zoneinfo import ZoneInfo
    from django.conf import settings
    
    text = text.lower().strip()
    
    # Use the configured timezone (Europe/London) instead of UTC
    tz = ZoneInfo(user_timezone or settings.TIME_ZONE)
    now = timezone.now().astimezone(tz)
    
    # Default time if only date is provided
    default_hour = 7
    default_minute = 0
    
    # Extract time component first
    time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    extracted_time = None
    
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        am_pm = time_match.group(3)
        
        if am_pm:
            if am_pm == 'pm' and hour != 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0
        
        extracted_time = (hour, minute)
    
    # Pattern 1: Relative time (in X hours/minutes/days/weeks)
    relative_match = re.search(r'in\s+(\d+)\s+(minute|minutes|hour|hours|day|days|week|weeks)', text)
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)
        
        if 'minute' in unit:
            return now + timedelta(minutes=amount)
        elif 'hour' in unit:
            return now + timedelta(hours=amount)
        elif 'day' in unit:
            result = now + timedelta(days=amount)
            if extracted_time:
                result = result.replace(hour=extracted_time[0], minute=extracted_time[1], second=0, microsecond=0)
            else:
                result = result.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)
            return result
        elif 'week' in unit:
            result = now + timedelta(weeks=amount)
            if extracted_time:
                result = result.replace(hour=extracted_time[0], minute=extracted_time[1], second=0, microsecond=0)
            else:
                result = result.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)
            return result
    
    # Pattern 2: Tomorrow
    if 'tomorrow' in text:
        result = now + timedelta(days=1)
        if extracted_time:
            return result.replace(hour=extracted_time[0], minute=extracted_time[1], second=0, microsecond=0)
        else:
            return result.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)
    
    # Pattern 3: Today
    if 'today' in text:
        if extracted_time:
            return now.replace(hour=extracted_time[0], minute=extracted_time[1], second=0, microsecond=0)
        else:
            # If "today" without time and it's past default hour, use current time + 1 hour
            if now.hour >= default_hour:
                return now + timedelta(hours=1)
            else:
                return now.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)
    
    # Pattern 4: Day of week (Monday, Tuesday, etc.)
    weekdays = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    for day_name, day_num in weekdays.items():
        if day_name in text:
            # Calculate days until target weekday
            current_weekday = now.weekday()
            days_ahead = day_num - current_weekday
            
            # If "next" is mentioned or the day has passed this week, go to next week
            if 'next' in text or days_ahead <= 0:
                days_ahead += 7
            
            result = now + timedelta(days=days_ahead)
            if extracted_time:
                return result.replace(hour=extracted_time[0], minute=extracted_time[1], second=0, microsecond=0)
            else:
                return result.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)
    
    # Pattern 5: Specific date (YYYY-MM-DD or MM/DD/YYYY or DD/MM/YYYY)
    date_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, text)
        if date_match:
            try:
                if '-' in pattern:  # YYYY-MM-DD
                    year, month, day = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                else:  # Assume MM/DD/YYYY for US format
                    month, day, year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                
                result = datetime(year, month, day)
                result = timezone.make_aware(result)
                
                if extracted_time:
                    return result.replace(hour=extracted_time[0], minute=extracted_time[1], second=0, microsecond=0)
                else:
                    return result.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)
            except ValueError:
                logger.warning(f"Invalid date values: {date_match.groups()}")
                continue
    
    # Pattern 6: Just a time (assume today if time is in future, tomorrow if past)
    if extracted_time:
        result = now.replace(hour=extracted_time[0], minute=extracted_time[1], second=0, microsecond=0)
        # If the time has already passed today, schedule for tomorrow
        if result <= now:
            result += timedelta(days=1)
        return result
    
    return None


def extract_reminder_details(text: str) -> Tuple[Optional[str], Optional[datetime]]:
    """
    Extract reminder task and datetime from natural language text.
    
    Examples:
        "Set a reminder to call mom tomorrow at 3pm"
        "Remind me to buy groceries next Monday"
        "Set reminder for meeting in 2 hours"
    
    Args:
        text: Natural language reminder request
        
    Returns:
        Tuple of (task_description, scheduled_datetime)
    """
    text_lower = text.lower().strip()
    
    # Define time-related keywords to help isolate the task
    time_keywords = r'(at|on|in|tomorrow|next|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)'
    
    # Patterns to extract the task. Order matters.
    task_patterns = [
        # Case 1: "... in {time} that/to {task}"
        r'in\s+\d+\s+(?:minute|hour|day|week)s?\s+(?:that|to)\s+(.+)',
        # Case 2: "... to {task} at/in/on {time}"
        r'(?:remind me to|reminder to)\s+(.+?)(?:\s+' + time_keywords + '|$)',
        # Case 3: "... that {task} at/in/on {time}"
        r'(?:remind me that|reminder that)\s+(.+?)(?:\s+' + time_keywords + '|$)',
        # Case 4: "... for/about {task} at/in/on {time}"
        r'(?:reminder for|reminder about)\s+(.+?)(?:\s+' + time_keywords + '|$)',
    ]

    task = None
    for pattern in task_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # The task is in the last captured group
            task = match.groups()[-1].strip()
            if task:
                break

    # If no specific task pattern matched, try a general fallback
    if not task:
        # Remove the initial trigger phrase
        fallback_text = re.sub(r'^(set a reminder|remind me)\s+', '', text, flags=re.IGNORECASE).strip()
        # Remove time expressions
        time_expression_pattern = r'(\s+' + time_keywords + r'\s+.*)$'
        task = re.sub(time_expression_pattern, '', fallback_text, flags=re.IGNORECASE).strip()

    # Final cleanup if task is still the full text
    if not task or task.lower() == text.lower():
        task = re.sub(r'^(set a reminder|remind me to|reminder for|reminder about)\s+', '', text, flags=re.IGNORECASE).strip()
    
    # Parse datetime
    scheduled_time = parse_reminder_datetime(text)
    
    return task, scheduled_time


def format_reminder_time(dt: datetime) -> str:
    """
    Format a datetime for display in a reminder notification.
    
    Args:
        dt: Datetime to format
        
    Returns:
        Formatted string like "Today at 3:00 PM" or "Monday, Oct 15 at 9:00 AM"
    """
    from zoneinfo import ZoneInfo
    from django.conf import settings
    
    # Convert to configured timezone for display
    tz = ZoneInfo(settings.TIME_ZONE)
    now = timezone.now().astimezone(tz)
    dt = dt.astimezone(tz)
    
    # Check if it's today
    if dt.date() == now.date():
        return dt.strftime("Today at %-I:%M %p")
    
    # Check if it's tomorrow
    if dt.date() == (now + timedelta(days=1)).date():
        return dt.strftime("Tomorrow at %-I:%M %p")
    
    # Check if it's within the next week
    if (dt - now).days < 7:
        return dt.strftime("%A at %-I:%M %p")
    
    # Otherwise, full date
    return dt.strftime("%A, %b %d at %-I:%M %p")
