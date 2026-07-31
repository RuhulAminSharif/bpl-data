import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.utils import set_page_config
from utils.read_data import (
    bpl_history_data,
    matches_list_data,
    matches_data,
    teams_data,
    players_data,
    venues_data,
    umpires_data,
    reserve_umpires_data,
    tv_umpire_data,
    match_referees_data,
    country_data,
)
from src.analysis.bpl_overview import (
    apply_custom_css,
    get_total_seasons,
    get_total_matches,
    get_total_teams,
    get_total_venues,
    get_total_cities,
    get_total_runs,
    get_total_wickets,
    get_match_time_distribution,
    get_highest_team_score,
    get_lowest_team_score,
    plot_bpl_winners_per_season,
    get_bpl_winner_per_season,
    get_most_titled_team,
    plot_most_titled_team,
    get_total_players,
    get_total_country,
    get_bangaladeshi_players_count,
)


# Load data
@st.cache_data(ttl=3600)
def fetch_bpl_data() -> tuple[
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
    pd.DataFrame,
]:
    bpl_history = bpl_history_data()
    matches_list = matches_list_data()
    matches = matches_data()
    teams = teams_data()
    players = players_data()
    venues = venues_data()
    umpires = umpires_data()
    reserve_umpires = reserve_umpires_data()
    tv_umpire = tv_umpire_data()
    match_referees = match_referees_data()
    country = country_data()
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
        country,
    )


def main():
    set_page_config()
    apply_custom_css()
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
            country,
        ) = fetch_bpl_data()
    except FileNotFoundError:
        st.error("Dataset files not found in data/ directory. Please add data.")
        st.stop()

    # Tabs
    # Dashboard Tabs
    (
        tab_overview,
        tab_team,
        tab_player,
        tab_venue,
        tab_season,
        tab_team_spec,
        tab_h2h,
    ) = st.tabs(
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

    with tab_overview:
        st.markdown(
            "<h2 style='text-align: center; margin-bottom: 25px;'>🏆 BPL Tournament Overview</h2>",
            unsafe_allow_html=True,
        )

        # Container 1: High Level Stats
        with st.container():
            st.markdown("#### 📈 Key Tournament Metrics")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Seasons", get_total_seasons(bpl_history))
            c2.metric("Matches Played", get_total_matches(matches))
            c3.metric("Total Runs Scored", f"{get_total_runs(matches):,}")
            c4.metric("Total Wickets Fallen", f"{get_total_wickets(matches):,}")
            c5.metric("Participating Teams", get_total_teams(teams))

            c6, c7, c8, c9, c10 = st.columns(5)
            total_players = get_total_players(players=players)
            total_bd_players = get_bangaladeshi_players_count(
                players=players, country=country
            )
            c6.metric("Players played", total_players)
            c7.metric("Players from", get_total_country(players=players), "countries")
            c8.metric(
                "Bangladeshi Players",
                total_bd_players,
            )
            c9.metric("Foreign Players", total_players - total_bd_players)
            c10.metric("Venues Used", get_total_venues(venues))
            
            c11, c12, c13, c14, c15 = st.columns(5)

            c11.metric("Host Cities", get_total_cities(venues))
            # Highest Team Score
            high_score = get_highest_team_score(matches, teams)
            if high_score:
                c12.metric(
                    "Highest Team Score",
                    f"{high_score['score']} Runs",
                    delta=high_score["team_name"],
                )
            low_score = get_lowest_team_score(matches, teams)

            if low_score:
                c13.metric(
                    label="Lowest Team Score (Completed)",
                    value=f"{low_score['score']} Runs",
                    delta=f"Team: {low_score['team_name']}",
                    delta_color="inverse",
                )
                st.info(
                    "Note: Abandoned matches or unplayed innings are excluded from the lowest score calculation."
                )
        st.markdown("---")

        # Container 2: Historical Championship Winners
        with st.container():
            col1, col2 = st.columns([1.2, 0.8])
            with col1:
                df_winners = get_bpl_winner_per_season(matches, teams, bpl_history)
                plot_bpl_winners_per_season(df_winners)
            with col2:
                df_titles = get_most_titled_team(matches, teams, bpl_history)
                plot_most_titled_team(df_titles)

        st.markdown("---")

        # Container 3: Match Schedule
        with st.container():
            get_match_time_distribution(matches)


if __name__ == "__main__":
    main()
