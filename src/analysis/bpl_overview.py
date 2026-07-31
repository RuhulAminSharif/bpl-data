import pandas as pd
import plotly.express as px
import streamlit as st


def apply_custom_css():
    """Injects custom CSS for styled metric cards and clean layout padding."""
    st.markdown(
        """
        <style>
            /* Custom styling for metric cards */
            div[data-testid="stMetric"] {
                background-color: rgba(151, 166, 186, 0.08);
                border: 1px solid rgba(151, 166, 186, 0.2);
                padding: 15px 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            div[data-testid="stMetric"]:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.1);
            }
            /* Subtitle headers */
            .section-header {
                font-size: 1.25rem;
                font-weight: 600;
                margin-top: 1rem;
                margin-bottom: 0.8rem;
                color: #2b2b2b;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_total_seasons(bpl_history: pd.DataFrame) -> int:
    return len(bpl_history) if not bpl_history.empty else 0


def get_total_runs(matches: pd.DataFrame) -> int:
    if matches.empty:
        return 0
    return int(matches["team1_score"].sum() + matches["team2_score"].sum())


def get_total_wickets(matches: pd.DataFrame) -> int:
    if matches.empty:
        return 0
    return int(matches["team1_wickets"].sum() + matches["team2_wickets"].sum())


def get_total_matches(matches: pd.DataFrame) -> int:
    return len(matches) if not matches.empty else 0


def get_total_teams(teams: pd.DataFrame) -> int:
    return len(teams) if not teams.empty else 0


def get_total_venues(venues: pd.DataFrame) -> int:
    return len(venues) if not venues.empty else 0


def get_total_cities(venues: pd.DataFrame) -> int:
    if not venues.empty and "town" in venues.columns:
        return int(venues["town"].dropna().nunique())
    return 0


def _extract_all_team_scores(matches: pd.DataFrame) -> pd.DataFrame:
    if matches.empty:
        return pd.DataFrame()

    t1 = matches[["match_id", "season_id", "team1_id", "team1_score"]].rename(
        columns={"team1_id": "team_id", "team1_score": "score"}
    )
    t2 = matches[["match_id", "season_id", "team2_id", "team2_score"]].rename(
        columns={"team2_id": "team_id", "team2_score": "score"}
    )

    return pd.concat([t1, t2], ignore_index=True).dropna(subset=["score"])


def get_highest_team_score(matches: pd.DataFrame, teams: pd.DataFrame) -> dict:
    all_scores = _extract_all_team_scores(matches)
    if all_scores.empty or teams.empty:
        return {}

    max_idx = all_scores["score"].idxmax()
    row = all_scores.loc[max_idx]

    team_match = teams[teams["team_id"] == row["team_id"]]
    team_name = team_match["team_name"].iloc[0] if not team_match.empty else "Unknown"

    return {"team_name": team_name, "score": int(row["score"])}


def get_lowest_team_score(matches: pd.DataFrame, teams: pd.DataFrame) -> dict:
    all_scores = _extract_all_team_scores(matches)
    valid_scores = all_scores[all_scores["score"] > 0]
    if valid_scores.empty or teams.empty:
        return {}

    min_idx = valid_scores["score"].idxmin()
    row = valid_scores.loc[min_idx]

    team_match = teams[teams["team_id"] == row["team_id"]]
    team_name = team_match["team_name"].iloc[0] if not team_match.empty else "Unknown"

    return {"team_name": team_name, "score": int(row["score"])}


def get_bpl_winner_per_season(
    matches: pd.DataFrame, teams: pd.DataFrame, bpl_history: pd.DataFrame
) -> pd.DataFrame:
    if matches.empty or teams.empty or bpl_history.empty:
        return pd.DataFrame()

    finals = matches[
        (matches["match_title"].str.lower() == "final")
        & (matches["match_winner_team_id"].notna())
    ].copy()

    if finals.empty:
        return pd.DataFrame()

    df = finals.merge(
        teams, left_on="match_winner_team_id", right_on="team_id", how="inner"
    ).drop_duplicates(subset=["season_id"], keep="first")

    df["season_id"] = pd.to_numeric(df["season_id"], errors="coerce")
    bpl_history["Season_ID"] = pd.to_numeric(bpl_history["Season_ID"], errors="coerce")

    return df.merge(
        bpl_history[["Season_ID", "Season"]],
        left_on="season_id",
        right_on="Season_ID",
        how="inner",
    ).sort_values("season_id")


def plot_bpl_winners_per_season(df: pd.DataFrame):
    if df.empty:
        st.info("No season winner data available.")
        return

    df["bar_height"] = 1

    fig = px.bar(
        df,
        x="Season",
        y="bar_height",
        color="team_name",
        text="team_name",
        title="<b>BPL Champions per Season</b>",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    fig.update_traces(
        texttemplate="%{text}",
        textposition="inside",
        insidetextanchor="middle",
        textangle=-90,
        textfont=dict(size=12, family="Arial Black"),
        hovertemplate="<b>Season:</b> %{x}<br><b>Winner:</b> %{text}<extra></extra>",
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="Season",
        yaxis_title="",
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        xaxis=dict(tickangle=-45, showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=10, r=10, t=50, b=50),
    )

    st.plotly_chart(fig, width="stretch")


def get_most_titled_team(
    matches: pd.DataFrame, teams: pd.DataFrame, bpl_history: pd.DataFrame
) -> pd.DataFrame:
    df = get_bpl_winner_per_season(
        matches=matches, teams=teams, bpl_history=bpl_history
    )
    if df.empty:
        return pd.DataFrame()
    return df["team_name"].value_counts().to_frame().reset_index()


def plot_most_titled_team(df_titles: pd.DataFrame):
    if df_titles.empty:
        st.info("No title data available.")
        return

    df_titles.columns = ["team_name", "count"]
    df_sorted = df_titles.sort_values(by="count", ascending=True)

    fig = px.bar(
        df_sorted,
        x="count",
        y="team_name",
        orientation="h",
        text="count",
        title="<b>Most Titles by Team</b>",
        color_discrete_sequence=["#e2a03f"],
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>Team:</b> %{y}<br><b>Titles:</b> %{x}<extra></extra>",
    )

    fig.update_layout(
        xaxis_title="Titles Won",
        yaxis_title="",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=10, r=20, t=50, b=50),
        xaxis=dict(showgrid=False, dtick=1),
        yaxis=dict(showgrid=False),
    )

    st.plotly_chart(fig, width="stretch")


def get_match_time_distribution(matches: pd.DataFrame):
    """Clean side-by-side metric breakdown + Donut Chart for Match Schedule."""
    if matches.empty or "floodlit" not in matches.columns:
        st.info("No match lighting/time data available.")
        return

    df_lighting = matches["floodlit"].dropna().astype(str).str.title().to_frame()
    if df_lighting.empty:
        st.info("No valid match time values found.")
        return

    counts_series = df_lighting["floodlit"].value_counts()
    df_counts = counts_series.reset_index()
    df_counts.columns = ["Lighting Condition", "Total Matches"]
    total_matches = len(df_lighting)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Match Schedule Breakdown")
        for _, row in df_counts.iterrows():
            condition = row["Lighting Condition"]
            match_cnt = row["Total Matches"]
            percentage = (match_cnt / total_matches) * 100
            icon = "🌕" if "night" in condition.lower() else "☀️"

            st.metric(
                label=f"{icon} {condition} Matches",
                value=f"{match_cnt} Matches",
                delta=f"{percentage:.1f}% of total matches",
            )

    with col2:
        fig = px.pie(
            df_counts,
            values="Total Matches",
            names="Lighting Condition",
            title="<b>Match Time Distribution</b>",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Pastel1,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>Condition:</b> %{label}<br><b>Count:</b> %{value}<extra></extra>",
        )

        fig.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=320,
            margin=dict(l=10, r=10, t=40, b=20),
        )

        st.plotly_chart(fig, width="stretch")


def get_total_players(players: pd.DataFrame) -> int:
    return len(players)


def get_total_country(players: pd.DataFrame) -> int:
    return len(players["countryId"].unique())


def get_bangaladeshi_players_count(players: pd.DataFrame, country: pd.DataFrame) -> int:
    bd = country[country["country"] == "Bangladesh"]

    # Get the countryId value
    if bd.empty:
        return 0  # Bangladesh not found in country table

    bd_country_id = bd["countryId"].iloc[0]

    # Filter players from Bangladesh
    local_players = players[players["countryId"] == bd_country_id]
    return len(local_players)
