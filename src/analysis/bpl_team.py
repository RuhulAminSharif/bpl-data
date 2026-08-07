import ast
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def get_team_trophies(team_id: int, matches: pd.DataFrame) -> int:
    """Calculates total BPL title trophies won by the selected team."""
    if matches.empty:
        return 0
    finals = matches[
        (matches["match_title"].astype(str).str.lower() == "final")
        & (matches["match_winner_team_id"].notna())
    ]
    if finals.empty:
        return 0
    return int((finals["match_winner_team_id"] == team_id).sum())


def get_team_comprehensive_stats(
    team_id: int,
    matches: pd.DataFrame,
    deliveries: pd.DataFrame,
    teams: pd.DataFrame,
    venues: pd.DataFrame,
) -> dict:
    """Calculates key metrics: Win/Loss/Ties, Toss impact, Preferred Venue (with wins count), Boundaries, Scores."""
    if matches.empty:
        return {}

    # Team Matches
    team_matches = matches[
        (matches["team1_id"] == team_id) | (matches["team2_id"] == team_id)
    ].copy()
    total_matches = len(team_matches)

    if total_matches == 0:
        return {}

    # Match Outcomes
    wins_df = matches[matches["match_winner_team_id"] == team_id]
    wins_count = len(wins_df)
    no_results = len(
        team_matches[
            team_matches["result_type"]
            .astype(str)
            .str.lower()
            .isin(["no result", "tie", "n/a", "abandoned"])
        ]
    )
    losses_count = total_matches - wins_count - no_results
    win_percentage = (wins_count / total_matches) * 100 if total_matches > 0 else 0.0

    # Most Matches Won Against
    opp_team_ids = wins_df.apply(
        lambda r: r["team2_id"] if r["team1_id"] == team_id else r["team1_id"], axis=1
    )
    most_win_opp_name = "N/A"
    most_win_opp_count = 0
    if not opp_team_ids.empty and not teams.empty:
        top_opp_id = opp_team_ids.value_counts().idxmax()
        most_win_opp_count = int(opp_team_ids.value_counts().max())
        opp_match = teams[teams["team_id"] == top_opp_id]
        if not opp_match.empty:
            most_win_opp_name = opp_match["team_name"].iloc[0]

    # Most Successful Venue (with Wins Count)
    most_fav_venue = "N/A"
    venue_col = "venue_id" if "venue_id" in wins_df.columns else "id"
    if not wins_df.empty and venue_col in wins_df.columns and not venues.empty:
        top_venue_id = wins_df[venue_col].value_counts().idxmax()
        venue_wins_count = int(wins_df[venue_col].value_counts().max())
        venue_id_col = "venue_id" if "venue_id" in venues.columns else "id"
        venue_match = venues[venues[venue_id_col] == top_venue_id]
        if not venue_match.empty:
            venue_name = venue_match["name"].iloc[0]
            most_fav_venue = f"{venue_name} ({venue_wins_count} Wins)"

    # Highest Score Against a Team
    highest_score = 0
    highest_score_opp = "N/A"
    t1_matches = matches[matches["team1_id"] == team_id]
    t2_matches = matches[matches["team2_id"] == team_id]

    for _, r in t1_matches.iterrows():
        if pd.notna(r["team1_score"]) and r["team1_score"] > highest_score:
            highest_score = int(r["team1_score"])
            opp = teams[teams["team_id"] == r["team2_id"]]
            highest_score_opp = opp["team_name"].iloc[0] if not opp.empty else "Unknown"

    for _, r in t2_matches.iterrows():
        if pd.notna(r["team2_score"]) and r["team2_score"] > highest_score:
            highest_score = int(r["team2_score"])
            opp = teams[teams["team_id"] == r["team1_id"]]
            highest_score_opp = opp["team_name"].iloc[0] if not opp.empty else "Unknown"

    # Boundaries (Deliveries Data)
    total_4s = 0
    total_6s = 0
    if not deliveries.empty and "team_id" in deliveries.columns:
        team_dels = deliveries[deliveries["team_id"] == team_id]
        total_4s = (
            int(team_dels["is_four"].sum()) if "is_four" in team_dels.columns else 0
        )
        total_6s = (
            int(team_dels["is_six"].sum()) if "is_six" in team_dels.columns else 0
        )

    return {
        "total_matches": total_matches,
        "wins": wins_count,
        "losses": losses_count,
        "no_results": no_results,
        "win_percentage": win_percentage,
        "most_win_against": f"{most_win_opp_name} ({most_win_opp_count} Wins)",
        "most_successful_venue": most_fav_venue,
        "highest_score_vs_opp": f"{highest_score} vs {highest_score_opp}",
        "total_4s": total_4s,
        "total_6s": total_6s,
    }


def get_team_indepth_toss_stats(team_id: int, matches: pd.DataFrame) -> dict:
    """Calculates granular toss & decision metrics."""
    if matches.empty:
        return {}

    team_matches = matches[
        (matches["team1_id"] == team_id) | (matches["team2_id"] == team_id)
    ].copy()

    if team_matches.empty:
        return {}

    # 1. TOSS MATRIX
    toss_won_df = team_matches[team_matches["toss_winner_team_id"] == team_id]
    toss_lost_df = team_matches[
        (team_matches["toss_winner_team_id"].notna())
        & (team_matches["toss_winner_team_id"] != team_id)
    ]

    toss_win_match_won = len(
        toss_won_df[toss_won_df["match_winner_team_id"] == team_id]
    )
    toss_win_match_lost = len(
        toss_won_df[
            (toss_won_df["match_winner_team_id"].notna())
            & (toss_won_df["match_winner_team_id"] != team_id)
        ]
    )

    toss_lost_match_won = len(
        toss_lost_df[toss_lost_df["match_winner_team_id"] == team_id]
    )
    toss_lost_match_lost = len(
        toss_lost_df[
            (toss_lost_df["match_winner_team_id"].notna())
            & (toss_lost_df["match_winner_team_id"] != team_id)
        ]
    )

    # 2. DECISION / INNINGS MATRIX
    bat_first_df = team_matches[team_matches["team1_id"] == team_id]
    bat_first_wins = len(bat_first_df[bat_first_df["match_winner_team_id"] == team_id])
    bat_first_losses = len(
        bat_first_df[
            (bat_first_df["match_winner_team_id"].notna())
            & (bat_first_df["match_winner_team_id"] != team_id)
        ]
    )

    field_first_df = team_matches[team_matches["team2_id"] == team_id]
    field_first_wins = len(
        field_first_df[field_first_df["match_winner_team_id"] == team_id]
    )
    field_first_losses = len(
        field_first_df[
            (field_first_df["match_winner_team_id"].notna())
            & (field_first_df["match_winner_team_id"] != team_id)
        ]
    )

    return {
        "toss_won_total": len(toss_won_df),
        "toss_won_match_won": toss_win_match_won,
        "toss_won_match_lost": toss_win_match_lost,
        "toss_lost_total": len(toss_lost_df),
        "toss_lost_match_won": toss_lost_match_won,
        "toss_lost_match_lost": toss_lost_match_lost,
        "bat_first_total": len(bat_first_df),
        "bat_first_wins": bat_first_wins,
        "bat_first_losses": bat_first_losses,
        "field_first_total": len(field_first_df),
        "field_first_wins": field_first_wins,
        "field_first_losses": field_first_losses,
    }


def plot_toss_impact_chart(toss_stats: dict):
    """Renders a Grouped Bar Chart comparing Outcomes by Toss Result."""
    if not toss_stats:
        return

    categories = ["Toss Won", "Toss Lost"]
    wins = [toss_stats["toss_won_match_won"], toss_stats["toss_lost_match_won"]]
    losses = [toss_stats["toss_won_match_lost"], toss_stats["toss_lost_match_lost"]]

    fig = go.Figure(
        data=[
            go.Bar(name="Match Won", x=categories, y=wins, marker_color="#2ea043"),
            go.Bar(name="Match Lost", x=categories, y=losses, marker_color="#da3633"),
        ]
    )

    fig.update_layout(
        title="<b>Match Outcome by Toss Result</b>",
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=280,
        margin=dict(l=10, r=10, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, width="stretch")


def plot_decision_impact_chart(toss_stats: dict):
    """Renders a Grouped Bar Chart comparing Outcomes by Batting/Fielding First."""
    if not toss_stats:
        return

    categories = ["Batting 1st", "Fielding 1st (Chasing)"]
    wins = [toss_stats["bat_first_wins"], toss_stats["field_first_wins"]]
    losses = [toss_stats["bat_first_losses"], toss_stats["field_first_losses"]]

    fig = go.Figure(
        data=[
            go.Bar(name="Match Won", x=categories, y=wins, marker_color="#2ea043"),
            go.Bar(name="Match Lost", x=categories, y=losses, marker_color="#da3633"),
        ]
    )

    fig.update_layout(
        title="<b>Match Outcome by Innings (Batting/Fielding)</b>",
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=280,
        margin=dict(l=10, r=10, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, width="stretch")


def _parse_player_ids(val) -> list[int]:
    """Safely parses player ID lists from string or list format."""
    if isinstance(val, list):
        return [int(x) for x in val if pd.notna(x)]
    if isinstance(val, str):
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [int(x) for x in parsed if pd.notna(x)]
        except (ValueError, SyntaxError):
            return []
    return []


def _get_team_match_player_pairs(
    team_id: int, matches: pd.DataFrame
) -> set[tuple[int, int]]:
    """Generates a set of (match_id, player_id) tuples strictly for the given team.

    This ensures a player's runs/wickets are only counted for the match they represented this team.
    """
    if matches.empty:
        return set()

    team_matches = matches[
        (matches["team1_id"] == team_id) | (matches["team2_id"] == team_id)
    ]

    valid_pairs = set()
    for _, row in team_matches.iterrows():
        m_id = row["match_id"]

        if row["team1_id"] == team_id and "team1_player_ids" in row:
            p_ids = _parse_player_ids(row["team1_player_ids"])
            for p_id in p_ids:
                valid_pairs.add((m_id, p_id))

        elif row["team2_id"] == team_id and "team2_player_ids" in row:
            p_ids = _parse_player_ids(row["team2_player_ids"])
            for p_id in p_ids:
                valid_pairs.add((m_id, p_id))

    return valid_pairs


def get_top_5_batters(
    team_id: int,
    deliveries: pd.DataFrame,
    matches: pd.DataFrame,
    players: pd.DataFrame,
) -> pd.DataFrame:
    """Returns Top 5 Run Scorers strictly for matches played for the selected team."""
    if (
        deliveries.empty
        or matches.empty
        or players.empty
        or "batter_id" not in deliveries.columns
    ):
        return pd.DataFrame()

    # Get valid (match_id, batter_id) pairs for this specific team
    valid_pairs = _get_team_match_player_pairs(team_id, matches)
    if not valid_pairs:
        return pd.DataFrame()

    # Create temporary match_player key in deliveries for fast filtering
    temp_dels = deliveries.copy()
    temp_dels["match_player"] = list(zip(temp_dels["match_id"], temp_dels["batter_id"]))

    # Filter deliveries matching the exact match & team player pairs
    team_dels = temp_dels[temp_dels["match_player"].isin(valid_pairs)]
    if team_dels.empty:
        return pd.DataFrame()

    top_batters = (
        team_dels.groupby("batter_id")["batsman_runs"]
        .sum()
        .reset_index()
        .sort_values(by="batsman_runs", ascending=False)
        .head(5)
    )

    return top_batters.merge(
        players[["player_id", "player_name"]],
        left_on="batter_id",
        right_on="player_id",
        how="inner",
    )[["player_name", "batsman_runs"]].rename(
        columns={"player_name": "Player", "batsman_runs": "Runs"}
    )


def get_top_5_bowlers(
    team_id: int,
    deliveries: pd.DataFrame,
    matches: pd.DataFrame,
    players: pd.DataFrame,
) -> pd.DataFrame:
    """Returns Top 5 Wicket Takers strictly for matches played for the selected team."""
    if (
        deliveries.empty
        or matches.empty
        or players.empty
        or "bowler_id" not in deliveries.columns
    ):
        return pd.DataFrame()

    valid_pairs = _get_team_match_player_pairs(team_id, matches)
    if not valid_pairs:
        return pd.DataFrame()

    # Filter for valid non-run-out wickets first
    wickets_df = deliveries[
        (deliveries["is_wicket"] == True)
        & (
            ~deliveries["wicket_kind"]
            .astype(str)
            .str.lower()
            .isin(["run out", "retired hurt"])
        )
    ].copy()

    if wickets_df.empty:
        return pd.DataFrame()

    # Create temporary match_player key
    wickets_df["match_player"] = list(
        zip(wickets_df["match_id"], wickets_df["bowler_id"])
    )

    team_bowl = wickets_df[wickets_df["match_player"].isin(valid_pairs)]
    if team_bowl.empty:
        return pd.DataFrame()

    top_bowlers = (
        team_bowl.groupby("bowler_id")["is_wicket"]
        .count()
        .reset_index()
        .sort_values(by="is_wicket", ascending=False)
        .head(5)
    )

    return top_bowlers.merge(
        players[["player_id", "player_name"]],
        left_on="bowler_id",
        right_on="player_id",
        how="inner",
    )[["player_name", "is_wicket"]].rename(
        columns={"player_name": "Player", "is_wicket": "Wickets"}
    )


def plot_season_wise_performance(
    team_id: int, matches: pd.DataFrame, bpl_history: pd.DataFrame
):
    """Generates a bar chart showing Matches Played vs Matches Won across each season."""
    if matches.empty or bpl_history.empty:
        st.info("No season history available.")
        return

    team_matches = matches[
        (matches["team1_id"] == team_id) | (matches["team2_id"] == team_id)
    ].copy()
    if team_matches.empty:
        return

    season_stats = []
    for s_id in team_matches["season_id"].unique():
        s_matches = team_matches[team_matches["season_id"] == s_id]
        played = len(s_matches)
        won = len(s_matches[s_matches["match_winner_team_id"] == team_id])

        s_name_row = bpl_history[bpl_history["Season_ID"] == s_id]
        s_name = (
            s_name_row["Season"].iloc[0] if not s_name_row.empty else f"Season {s_id}"
        )

        season_stats.append(
            {"Season": str(s_name), "Played": played, "Won": won, "Lost": played - won}
        )

    df_season = pd.DataFrame(season_stats).sort_values(by="Season")

    fig = px.bar(
        df_season,
        x="Season",
        y=["Won", "Lost"],
        title="<b>Season-by-Season Performance</b>",
        barmode="group",
        color_discrete_map={"Won": "#2ea043", "Lost": "#da3633"},
    )
    fig.update_layout(
        xaxis_title="Season",
        yaxis_title="Matches",
        legend_title="",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=320,
        margin=dict(l=10, r=10, t=40, b=20),
    )
    st.plotly_chart(fig, width="stretch")
