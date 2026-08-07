import pandas as pd
import streamlit as st

from src.analysis.bpl_overview import (
    get_bangaladeshi_players_count,
    get_bpl_winner_per_season,
    get_highest_individual_score,
    get_highest_team_score,
    get_lowest_team_score,
    get_match_time_distribution,
    get_most_100s_player,
    get_most_4s_in_match_player,
    get_most_4s_player,
    get_most_50s_player,
    get_most_6s_in_match_player,
    get_most_6s_player,
    get_most_catches_player,
    get_most_potm_player,
    get_most_runs_player,
    get_most_titled_team,
    get_most_wickets_player,
    get_total_cities,
    get_total_country,
    get_total_fours,
    get_total_matches,
    get_total_players,
    get_total_runs,
    get_total_seasons,
    get_total_sixes,
    get_total_teams,
    get_total_venues,
    get_total_wickets,
    plot_bpl_winners_per_season,
    plot_most_titled_team,
    plot_match_time_distribution,
)

from src.analysis.bpl_team import (
    get_team_comprehensive_stats,
    get_team_indepth_toss_stats,
    get_team_trophies,
    get_top_5_batters,
    get_top_5_bowlers,
    plot_decision_impact_chart,
    plot_season_wise_performance,
    plot_toss_impact_chart,
)
from utils.read_data import (
    bpl_history_data,
    country_data,
    deliveries_data,
    match_referees_data,
    matches_data,
    matches_list_data,
    players_data,
    reserve_umpires_data,
    teams_data,
    tv_umpire_data,
    umpires_data,
    venues_data,
)
from utils.utils import apply_custom_css, render_feature_card, set_page_config


@st.cache_data(ttl=3600)
def fetch_bpl_data() -> tuple:
    return (
        bpl_history_data(),
        matches_list_data(),
        matches_data(),
        teams_data(),
        players_data(),
        venues_data(),
        umpires_data(),
        reserve_umpires_data(),
        tv_umpire_data(),
        match_referees_data(),
        country_data(),
        deliveries_data(),
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
            deliveries,
        ) = fetch_bpl_data()
    except FileNotFoundError:
        st.error("Dataset files not found in data/ directory. Please add data.")
        st.stop()

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
        # ---------------------------------------------------------------------
        # ZONE 1: TOP MACRO METRICS (Matching Custom CSS Cards)
        # ---------------------------------------------------------------------
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            render_feature_card(
                "Total Seasons", get_total_seasons(bpl_history), icon="📅"
            )
        with c2:
            render_feature_card("Total Matches", get_total_matches(matches), icon="🏏")
        with c3:
            render_feature_card("Total Runs", f"{get_total_runs(matches):,}", icon="⚡")
        with c4:
            render_feature_card(
                "Total Wickets", f"{get_total_wickets(matches):,}", icon="🎯"
            )
        with c5:
            tot_boundaries = get_total_fours(deliveries) + get_total_sixes(deliveries)
            render_feature_card("Total Boundaries", f"{tot_boundaries:,}", icon="💥")

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # ZONE 2: PLAYER & MATCH RECORD CARDS
        # ---------------------------------------------------------------------
        st.markdown("### 🌟 All-Time Tournament Records")

        rec_tab1, rec_tab2, rec_tab3 = st.tabs(
            ["🏏 Batting Hall of Fame", "🎯 Bowling & Fielding", "🏢 Team Records"]
        )

        most_runs = get_most_runs_player(deliveries, players) or {}
        most_wickets = get_most_wickets_player(deliveries, players) or {}
        most_4s = get_most_4s_player(deliveries, players) or {}
        most_6s = get_most_6s_player(deliveries, players) or {}
        highest_ind = get_highest_individual_score(deliveries, players) or {}
        most_50s = get_most_50s_player(deliveries, players) or {}
        most_100s = get_most_100s_player(deliveries, players) or {}
        most_catches = get_most_catches_player(deliveries, players) or {}
        most_potm = get_most_potm_player(matches, players) or {}
        high_team = get_highest_team_score(matches, teams) or {}
        low_team = get_lowest_team_score(matches, teams) or {}

        with rec_tab1:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                render_feature_card(
                    "Most Tournament Runs",
                    f"{most_runs.get('total_runs', 'N/A')} Runs",
                    subtitle=most_runs.get("player_name"),
                    icon="🔥",
                )
                render_feature_card(
                    "Highest Individual Score",
                    f"{highest_ind.get('highest_score', 'N/A')}*",
                    subtitle=highest_ind.get("player_name"),
                    icon="⚡",
                )
            with col2:
                render_feature_card(
                    "Most Fours Hit",
                    f"{most_4s.get('total_fours', 'N/A')} Fours",
                    subtitle=most_4s.get("player_name"),
                    icon="🏏",
                )
                render_feature_card(
                    "Most Fifties (50s)",
                    f"{most_50s.get('total_50s', 'N/A')} Fifties",
                    subtitle=most_50s.get("player_name"),
                    icon="🎖️",
                )
            with col3:
                render_feature_card(
                    "Most Sixes Hit",
                    f"{most_6s.get('total_sixes', 'N/A')} Sixes",
                    subtitle=most_6s.get("player_name"),
                    icon="🚀",
                )
                render_feature_card(
                    "Most Hundreds (100s)",
                    f"{most_100s.get('total_100s', 'N/A')} Hundreds",
                    subtitle=most_100s.get("player_name"),
                    icon="💯",
                )
            with col4:
                most_4s_match = get_most_4s_in_match_player(deliveries, players) or {}
                most_6s_match = get_most_6s_in_match_player(deliveries, players) or {}

                render_feature_card(
                    "Most 4s in a Match",
                    f"{most_4s_match.get('most_fours_in_match', 'N/A')} Fours",
                    subtitle=most_4s_match.get("player_name"),
                    icon="⏱️",
                )
                render_feature_card(
                    "Most 6s in a Match",
                    f"{most_6s_match.get('most_sixes_in_match', 'N/A')} Sixes",
                    subtitle=most_6s_match.get("player_name"),
                    icon="💥",
                )

        with rec_tab2:
            col1, col2, col3 = st.columns(3)
            with col1:
                render_feature_card(
                    "Most Wickets Taken",
                    f"{most_wickets.get('total_wickets', 'N/A')} Wickets",
                    subtitle=most_wickets.get("player_name"),
                    icon="🎯",
                )
            with col2:
                render_feature_card(
                    "Most Catches Taken",
                    f"{most_catches.get('total_catches', 'N/A')} Catches",
                    subtitle=most_catches.get("player_name"),
                    icon="🖐️",
                )
            with col3:
                render_feature_card(
                    "Most Player of Match",
                    f"{most_potm.get('total_potm', 'N/A')} Awards",
                    subtitle=most_potm.get("player_name"),
                    icon="🥇",
                )

        with rec_tab3:
            col1, col2 = st.columns(2)
            with col1:
                render_feature_card(
                    "Highest Team Score",
                    f"{high_team.get('score', 'N/A')} Runs",
                    subtitle=high_team.get("team_name"),
                    icon="📈",
                )
            with col2:
                render_feature_card(
                    "Lowest Team Score",
                    f"{low_team.get('score', 'N/A')} Runs",
                    subtitle=low_team.get("team_name"),
                    badge="Completed Innings",
                    icon="📉",
                )

        st.markdown("---")

        # ---------------------------------------------------------------------
        # ZONE 3: CHARTS & DEMOGRAPHICS
        # ---------------------------------------------------------------------
        with st.container():
            col1, col2 = st.columns([1.2, 0.8])
            with col1:
                df_winners = get_bpl_winner_per_season(matches, teams, bpl_history)
                plot_bpl_winners_per_season(df_winners)
            with col2:
                df_titles = get_most_titled_team(matches, teams, bpl_history)
                plot_most_titled_team(df_titles)

        st.markdown("---")

        # Demographics Metrics
        st.markdown("### 🌍 Player Demographics & Geography")
        d1, d2, d3, d4, d5 = st.columns(5)

        total_players = get_total_players(players=players)
        total_bd = get_bangaladeshi_players_count(players=players, country=country)

        with d1:
            render_feature_card("Total Players", total_players, icon="👤")
        with d2:
            render_feature_card("Bangladeshi Players", total_bd, icon="🇧🇩")
        with d3:
            render_feature_card("Foreign Players", total_players - total_bd, icon="✈️")
        with d4:
            render_feature_card(
                "Countries", get_total_country(players=players), icon="🌐"
            )
        with d5:
            render_feature_card(
                "Venues / Cities",
                f"{get_total_venues(venues)} / {get_total_cities(venues)}",
                icon="🏟️",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Match Schedule & Lighting Conditions
        st.markdown("### ☀️ Match Schedule & Lighting Conditions")
        df_counts, lighting_summary = get_match_time_distribution(matches)

        if not df_counts.empty:
            col_metrics, col_chart = st.columns([1, 1], vertical_alignment="center")

            with col_metrics:
                total_m = sum(lighting_summary.values())
                m_cols = st.columns(len(lighting_summary))

                for idx, (condition, count) in enumerate(lighting_summary.items()):
                    icon = "🌕" if "night" in str(condition).lower() else "☀️"
                    pct = (count / total_m) * 100 if total_m > 0 else 0

                    with m_cols[idx]:
                        render_feature_card(
                            title=f"{condition} Matches",
                            value=f"{count}",
                            subtitle=f"{pct:.1f}% of matches",
                            icon=icon,
                        )

            with col_chart:
                plot_match_time_distribution(df_counts)

    with tab_team:
        st.markdown(
            "<h2 style='text-align: center; margin-bottom: 20px;'>📊 Team Comprehensive Analysis</h2>",
            unsafe_allow_html=True,
        )

        if teams.empty:
            st.info("No team data available.")
        else:
            selected_team_name = st.selectbox(
                "🏏 Select Team:",
                options=teams["team_name"].tolist(),
                index=0,
            )

            selected_team_row = teams[teams["team_name"] == selected_team_name].iloc[0]
            selected_team_id = int(selected_team_row["team_id"])

            trophies = get_team_trophies(selected_team_id, matches)
            stats = get_team_comprehensive_stats(
                selected_team_id, matches, deliveries, teams, venues
            )

            if stats:
                st.markdown("---")

                # -------------------------------------------------------------
                # SECTION 1: KEY TEAM HIGHLIGHTS
                # -------------------------------------------------------------
                st.markdown("### 🏆 Franchise Overview & Highlights")
                c1, c2, c3, c4, c5 = st.columns(5)

                with c1:
                    render_feature_card("BPL Titles", f"{trophies} Trophies", icon="🏆")
                with c2:
                    render_feature_card(
                        "Matches Played", stats["total_matches"], icon="🏏"
                    )
                with c3:
                    render_feature_card(
                        "Matches Won / Lost",
                        f"{stats['wins']} W - {stats['losses']} L",
                        subtitle=f"Ties/NR: {stats['no_results']}",
                        icon="✅",
                    )
                with c4:
                    render_feature_card(
                        "Win Percentage",
                        f"{stats['win_percentage']:.1f}%",
                        icon="📈",
                    )
                with c5:
                    render_feature_card(
                        "Boundaries (4s / 6s)",
                        f"{stats['total_4s']} / {stats['total_6s']}",
                        icon="💥",
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                c6, c7, c8 = st.columns(3)
                with c6:
                    render_feature_card(
                        "Most Wins Against",
                        stats["most_win_against"],
                        icon="🗡️",
                    )
                with c7:
                    render_feature_card(
                        "Preferred Venue",
                        stats["most_successful_venue"],  # Includes (X Wins)
                        icon="🏟️",
                    )
                with c8:
                    render_feature_card(
                        "Highest Team Score",
                        stats["highest_score_vs_opp"],
                        icon="🔥",
                    )

                st.markdown("---")

                # -------------------------------------------------------------
                # SECTION 2: TOSS & DECISION ANALYSIS
                # -------------------------------------------------------------
                st.markdown("### 🪙 In-Depth Toss & Decision Analysis")
                toss_stats = get_team_indepth_toss_stats(selected_team_id, matches)

                if toss_stats:
                    # Win Rate Calculations
                    tw_pct = (
                        (
                            toss_stats["toss_won_match_won"]
                            / toss_stats["toss_won_total"]
                            * 100
                        )
                        if toss_stats["toss_won_total"] > 0
                        else 0
                    )
                    tl_pct = (
                        (
                            toss_stats["toss_lost_match_won"]
                            / toss_stats["toss_lost_total"]
                            * 100
                        )
                        if toss_stats["toss_lost_total"] > 0
                        else 0
                    )
                    bat_pct = (
                        (
                            toss_stats["bat_first_wins"]
                            / toss_stats["bat_first_total"]
                            * 100
                        )
                        if toss_stats["bat_first_total"] > 0
                        else 0
                    )
                    field_pct = (
                        (
                            toss_stats["field_first_wins"]
                            / toss_stats["field_first_total"]
                            * 100
                        )
                        if toss_stats["field_first_total"] > 0
                        else 0
                    )

                    tc1, tc2, tc3, tc4 = st.columns(4)

                    with tc1:
                        render_feature_card(
                            title="Toss Won Record",
                            value=f"{toss_stats['toss_won_match_won']}W - {toss_stats['toss_won_match_lost']}L",
                            subtitle=f"{tw_pct:.1f}% Win Rate",
                            icon="🪙",
                        )
                    with tc2:
                        render_feature_card(
                            title="Toss Lost Record",
                            value=f"{toss_stats['toss_lost_match_won']}W - {toss_stats['toss_lost_match_lost']}L",
                            subtitle=f"{tl_pct:.1f}% Win Rate",
                            icon="🔥",
                        )
                    with tc3:
                        render_feature_card(
                            title="Batting 1st Record",
                            value=f"{toss_stats['bat_first_wins']}W - {toss_stats['bat_first_losses']}L",
                            subtitle=f"{bat_pct:.1f}% Win Rate",
                            icon="🏏",
                        )
                    with tc4:
                        render_feature_card(
                            title="Fielding 1st Record",
                            value=f"{toss_stats['field_first_wins']}W - {toss_stats['field_first_losses']}L",
                            subtitle=f"{field_pct:.1f}% Win Rate",
                            icon="🏃",
                        )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Charts
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        plot_toss_impact_chart(toss_stats)
                    with chart_col2:
                        plot_decision_impact_chart(toss_stats)

                st.markdown("---")

                # -------------------------------------------------------------
                # SECTION 3: TOP PERFORMERS & SEASON PROGRESS
                # -------------------------------------------------------------
                col_left, col_right = st.columns([1, 1])

                with col_left:
                    st.markdown("### 🌟 All-Time Top Performers")
                    top_batters = get_top_5_batters(
                        selected_team_id, deliveries, matches, players
                    )
                    top_bowlers = get_top_5_bowlers(
                        selected_team_id, deliveries, matches, players
                    )

                    bat_tab, bowl_tab = st.tabs(
                        ["🏏 Top 5 Batters", "🎯 Top 5 Bowlers"]
                    )
                    with bat_tab:
                        if not top_batters.empty:
                            st.dataframe(
                                top_batters,
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.info("No batting records found for this team.")

                    with bowl_tab:
                        if not top_bowlers.empty:
                            st.dataframe(
                                top_bowlers,
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.info("No bowling records found for this team.")

                with col_right:
                    st.markdown("### 📅 Season Progress")
                    plot_season_wise_performance(selected_team_id, matches, bpl_history)

            else:
                st.warning("No performance record found for this team.")


if __name__ == "__main__":
    main()
