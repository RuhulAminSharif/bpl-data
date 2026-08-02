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


def get_match_time_distribution(matches: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Pure data function: Extracts lighting condition counts and percentages."""
    if matches.empty or "floodlit" not in matches.columns:
        return pd.DataFrame(), {}

    df_lighting = matches["floodlit"].dropna().astype(str).str.title().to_frame()
    if df_lighting.empty:
        return pd.DataFrame(), {}

    counts_series = df_lighting["floodlit"].value_counts()
    df_counts = counts_series.reset_index()
    df_counts.columns = ["Lighting Condition", "Total Matches"]

    total_matches = len(df_lighting)
    df_counts["Percentage"] = (df_counts["Total Matches"] / total_matches) * 100

    # Summary dict for quick UI metrics: {'Day': 45, 'Night': 120, ...}
    metrics_summary = counts_series.to_dict()

    return df_counts, metrics_summary


def plot_match_time_distribution(df_counts: pd.DataFrame):
    """Pure plotting function: Renders a compact Donut Chart."""
    if df_counts.empty:
        st.info("No match time distribution data available.")
        return

    fig = px.pie(
        df_counts,
        values="Total Matches",
        names="Lighting Condition",
        hole=0.5,  # Donut style
        color_discrete_sequence=px.colors.qualitative.Pastel1,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}:</b> %{value} Matches (%{percent})<extra></extra>",
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=260,  # Compact height to save vertical UI space
        margin=dict(l=10, r=10, t=10, b=10),
    )

    st.plotly_chart(fig, width="content")


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


def get_total_fours(deliveries: pd.DataFrame) -> int:
    """
    #### Returns:
    Total fours hit.
    """
    if deliveries.empty or "is_four" not in deliveries.columns:
        return 0
    return deliveries["is_four"].sum()


def get_total_sixes(deliveries: pd.DataFrame) -> int:
    """
    #### Returns:
    Total sixes hit.
    """
    if deliveries.empty or "is_six" not in deliveries.columns:
        return 0
    return deliveries["is_six"].sum()


def get_most_runs_player(deliveries: pd.DataFrame, players: pd.DataFrame) -> dict:
    if deliveries.empty or players.empty:
        return {}

    # Count total runs per player
    runs_count = (
        deliveries.groupby("batter_id")["batsman_runs"]
        .sum()
        .reset_index(name="total_runs")
        .sort_values(by="total_runs", ascending=False)
    )

    # Merge with players to get player names
    result = runs_count.merge(
        players[["player_id", "player_name"]],
        left_on="batter_id",
        right_on="player_id",
        how="left",
    )

    return (
        result[["player_name", "total_runs"]].head(1).to_dict(orient="records")[0]
        if not result.empty
        else {}
    )


def get_most_wickets_player(deliveries: pd.DataFrame, players: pd.DataFrame) -> dict:
    if deliveries.empty or players.empty:
        return {}

    # Count total wickets per player
    wickets_count = (
        deliveries.groupby("bowler_id")["is_wicket"]
        .sum()
        .reset_index(name="total_wickets")
        .sort_values(by="total_wickets", ascending=False)
    )

    # Merge with players to get player names
    result = wickets_count.merge(
        players[["player_id", "player_name"]],
        left_on="bowler_id",
        right_on="player_id",
        how="left",
    )

    return (
        result[["player_name", "total_wickets"]].head(1).to_dict(orient="records")[0]
        if not result.empty
        else {}
    )


def get_most_catches_player(deliveries: pd.DataFrame, players: pd.DataFrame) -> dict:
    # wicket_kind -> caught
    if deliveries.empty or players.empty:
        return {}

    if (
        "wicket_kind" not in deliveries.columns
        or "fielder_id" not in deliveries.columns
    ):
        return {}

    caught_deliveries = deliveries[
        deliveries["wicket_kind"].astype(str).str.lower() == "caught"
    ]

    if caught_deliveries.empty:
        return {}

    catches_count = (
        caught_deliveries.groupby("fielder_id")
        .size()
        .reset_index(name="total_catches")
        .sort_values(by="total_catches", ascending=False)
    )

    result = catches_count.merge(
        players[["player_id", "player_name"]],
        left_on="fielder_id",
        right_on="player_id",
        how="left",
    )

    return (
        result[["player_name", "total_catches"]].head(1).to_dict(orient="records")[0]
        if not result.empty
        else {}
    )


def get_most_4s_player(deliveries: pd.DataFrame, players: pd.DataFrame) -> dict:
    if deliveries.empty or players.empty:
        return {}

    # Filter deliveries for fours
    fours_deliveries = deliveries[deliveries["is_four"] == True]

    # Count fours per player
    fours_count = (
        fours_deliveries.groupby("batter_id")
        .size()
        .reset_index(name="total_fours")
        .sort_values(by="total_fours", ascending=False)
    )

    # Merge with players to get player names
    result = fours_count.merge(
        players[["player_id", "player_name"]],
        left_on="batter_id",
        right_on="player_id",
        how="left",
    )

    return (
        result[["player_name", "total_fours"]].head(1).to_dict(orient="records")[0]
        if not result.empty
        else {}
    )


def get_most_6s_player(deliveries: pd.DataFrame, players: pd.DataFrame) -> dict:
    if deliveries.empty or players.empty:
        return {}

    # Filter deliveries for sixes
    sixes_deliveries = deliveries[deliveries["is_six"] == True]

    # Count sixes per player
    sixes_count = (
        sixes_deliveries.groupby("batter_id")
        .size()
        .reset_index(name="total_sixes")
        .sort_values(by="total_sixes", ascending=False)
    )

    # Merge with players to get player names
    result = sixes_count.merge(
        players[["player_id", "player_name"]],
        left_on="batter_id",
        right_on="player_id",
        how="left",
    )

    return (
        result[["player_name", "total_sixes"]].head(1).to_dict(orient="records")[0]
        if not result.empty
        else {}
    )


def get_most_potm_player(matches: pd.DataFrame, players: pd.DataFrame) -> dict:
    if matches.empty or players.empty:
        return {}

    potm_count = (
        matches.groupby("player_of_match_id")
        .size()
        .reset_index(name="total_potm")
        .sort_values(by="total_potm", ascending=False)
    )

    result = potm_count.merge(
        players[["player_id", "player_name"]],
        left_on="player_of_match_id",
        right_on="player_id",
        how="left",
    )

    return (
        result[["player_name", "total_potm"]].head(1).to_dict(orient="records")[0]
        if not result.empty
        else {}
    )


def get_highest_individual_score(
    deliveries: pd.DataFrame, players: pd.DataFrame
) -> dict:
    if deliveries.empty or players.empty:
        return {}

    # Calculate total runs per player in each match
    player_match_runs = (
        deliveries.groupby(["match_id", "batter_id"])["batsman_runs"]
        .sum()
        .reset_index(name="total_runs")
    )

    # Find the highest individual score
    max_score_row = player_match_runs.loc[player_match_runs["total_runs"].idxmax()]

    # Get player name
    player_info = players[players["player_id"] == max_score_row["batter_id"]]
    player_name = (
        player_info["player_name"].iloc[0] if not player_info.empty else "Unknown"
    )

    return {
        "player_name": player_name,
        "match_id": int(max_score_row["match_id"]),
        "highest_score": int(max_score_row["total_runs"]),
    }


def get_most_50s_player(deliveries: pd.DataFrame, players: pd.DataFrame) -> dict:
    if deliveries.empty or players.empty:
        return {}

    # Calculate total runs per player in each match and count innings with 50 or more
    innings_runs = (
        deliveries.groupby(["match_id", "batter_id"])["batsman_runs"]
        .sum()
        .reset_index(name="total_runs")
    )

    fifties_count = (
        innings_runs[innings_runs["total_runs"] >= 50]
        .groupby("batter_id")
        .size()
        .reset_index(name="total_50s")
        .sort_values(by="total_50s", ascending=False)
    )

    # Merge with players to get player names
    result = fifties_count.merge(
        players[["player_id", "player_name"]],
        left_on="batter_id",
        right_on="player_id",
        how="left",
    )

    return (
        result[["player_name", "total_50s"]].head(1).to_dict(orient="records")[0]
        if not result.empty
        else {}
    )


def get_most_100s_player(deliveries: pd.DataFrame, players: pd.DataFrame) -> dict:
    if deliveries.empty or players.empty:
        return {}

    innings_runs = (
        deliveries.groupby(["match_id", "batter_id"])["batsman_runs"]
        .sum()
        .reset_index(name="total_runs")
    )

    # Count the number of 100s per player
    hundreds_count = (
        innings_runs[innings_runs["total_runs"] >= 100]
        .groupby("batter_id")
        .size()
        .reset_index(name="total_100s")
        .sort_values(by="total_100s", ascending=False)
    )

    # Merge with players to get player names
    result = hundreds_count.merge(
        players[["player_id", "player_name"]],
        left_on="batter_id",
        right_on="player_id",
        how="left",
    )

    return (
        result[["player_name", "total_100s"]].head(1).to_dict(orient="records")[0]
        if not result.empty
        else {}
    )


def get_most_4s_in_match_player(
    deliveries: pd.DataFrame, players: pd.DataFrame
) -> dict:
    if deliveries.empty or players.empty:
        return {}

    # Count the number of 4s per player in each match
    fours_count = (
        deliveries[deliveries["is_four"] == True]
        .groupby(["match_id", "batter_id"])
        .size()
        .reset_index(name="total_fours")
        .sort_values(by="total_fours", ascending=False)
    )

    # Get the player with the most 4s in a single match
    max_fours_row = fours_count.loc[fours_count["total_fours"].idxmax()]

    # Get player name
    player_info = players[players["player_id"] == max_fours_row["batter_id"]]
    player_name = (
        player_info["player_name"].iloc[0] if not player_info.empty else "Unknown"
    )

    return {
        "player_name": player_name,
        "match_id": int(max_fours_row["match_id"].item()),
        "most_fours_in_match": int(max_fours_row["total_fours"].item()),
    }


def get_most_6s_in_match_player(
    deliveries: pd.DataFrame, players: pd.DataFrame
) -> dict:
    if deliveries.empty or players.empty:
        return {}

    # Count the number of 6s per player in each match
    sixes_count = (
        deliveries[deliveries["is_six"] == True]
        .groupby(["match_id", "batter_id"])
        .size()
        .reset_index(name="total_sixes")
        .sort_values(by="total_sixes", ascending=False)
    )

    # Get the player with the most 6s in a single match
    max_sixes_row = sixes_count.loc[sixes_count["total_sixes"].idxmax()]

    # Get player name
    player_info = players[players["player_id"] == max_sixes_row["batter_id"]]
    player_name = (
        player_info["player_name"].iloc[0] if not player_info.empty else "Unknown"
    )

    return {
        "player_name": player_name,
        "match_id": int(max_sixes_row["match_id"].item()),
        "most_sixes_in_match": int(max_sixes_row["total_sixes"].item()),
    }
