from datetime import datetime
import streamlit as st
import base64
import os


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


def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None


def set_page_config():
    # Set page config
    st.set_page_config(
        page_title="BPL Analysis Dashboard", page_icon="🏏", layout="wide"
    )

    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "images"))
    logo_path = os.path.join(base_path, "bpl_logo.jpg")

    encoded_image = get_base64_image(logo_path)

    # Render Header
    if encoded_image:
        st.markdown(
            f"""
            <div style='text-align: center;'>
                <img src='data:image/jpeg;base64,{encoded_image}' width='180' height='100' style='object-fit: contain;'/>
                <h1 style='margin-top:10px;'>BPL Data Analysis Dashboard (2012-2026)</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<h1 style='text-align: center;'>BPL Data Analysis Dashboard (2012-2026)</h1>",
            unsafe_allow_html=True,
        )
