from datetime import datetime

def extract_series_slug(link: str) -> str:
    """Extract the series slug from a Cricinfo URL link."""
    return str(link).split("/")[-2]

def parse_time_info(time_dict: dict) -> dict:
    """Parse time information from the match API response."""
    if not time_dict or "startTime" not in time_dict:
        return {}

    start_utc = datetime.fromisoformat(time_dict["startTime"])
    return {
        "match_date": start_utc.strftime("%Y-%m-%d"),
        "match_start_utc": start_utc,
        "scheduled_overs": time_dict.get("scheduledOvers"),
        "lighting": time_dict.get("floodlit"),
        "session_schedule_raw": time_dict.get("hoursInfo"),
    }
