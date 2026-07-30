import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_loader import load_data
from utils.utils import set_page_config


# Load data
@st.cache_data(ttl=3600)
def get_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    bpl_data: dict[str, pd.DataFrame] = load_data()
    matches = bpl_data["matches"]
    matches_list = bpl_data["matches_list"]
    match_referees = bpl_data["match_referees"]
    venues = bpl_data["venues"]
    tv_umpire = bpl_data["tv_umpire"]
    players = bpl_data["players"]
    bpl_history = bpl_data["bpl_history"]
    teams = bpl_data["teams"]
    umpires = bpl_data["umpires"]
    reserve_umpires = bpl_data["reserve_umpires"]
    return (
        bpl_history,
        matches_list,
        matches,
        teams,
        players,
        venues,
        umpires,
        reserve_umpires,
        tv_umpire,
        match_referees,
    )


def main():
    set_page_config()
    try:
        (
            bpl_history,
            matches_list,
            matches,
            teams,
            players,
            venues,
            umpires,
            reserve_umpires,
            tv_umpire,
            match_referees,
        ) = get_data()
    except FileNotFoundError:
        st.error("Dataset files not found in data/ directory. Please add data.")
        st.stop()

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "🏠 Overview",
            "📊 Team Analysis",
            "👤 Player Stats",
            "🏟️ Venue Insights",
            "📅 Season Analysis",
            "🏏 Team-Specific Analysis",
            "🤝 Head-to-Head Analysis",
        ]
    )
    with tab1:
        st.subheader("BPL Tournament Summary")
        st.write(f"Total Matches Analyzed: **{len(matches)}**")
        st.dataframe(matches.head(10), use_container_width=True)


if __name__ == "__main__":
    main()
