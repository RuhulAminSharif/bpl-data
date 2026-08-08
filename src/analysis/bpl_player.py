import ast
import numpy as np
import pandas as pd


def _parse_player_ids(val) -> list[int]:
    """parses player ID lists from string or list format."""
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


def get_player_matches(player_id: int, matches: pd.DataFrame) -> pd.DataFrame:
    """Returns all matches in which the player participated, including the team_id they represented."""
    if matches.empty:
        return pd.DataFrame()

    matched_rows = []
    for _, row in matches.iterrows():
        p1 = _parse_player_ids(row.get("team1_player_ids", []))
        p2 = _parse_player_ids(row.get("team2_player_ids", []))

        if player_id in p1:
            matched_rows.append((row["match_id"], row["team1_id"]))
        elif player_id in p2:
            matched_rows.append((row["match_id"], row["team2_id"]))

    if not matched_rows:
        return pd.DataFrame()

    df_player_matches = pd.DataFrame(matched_rows, columns=["match_id", "team_id"])
    return df_player_matches.merge(matches, on="match_id", how="inner")


def _calc_fielding_stats(
    player_id: int, fielding_dels: pd.DataFrame
) -> tuple[int, int]:
    """calculates total catches and stumpings for a player."""
    if fielding_dels.empty:
        return 0, 0

    # 1. Detect Dismissal Kind Column
    dismissal_col = "wicket_kind"
    d_kind = fielding_dels[dismissal_col].astype(str).str.lower().str.strip()

    catches = 0
    stumpings = 0

    # 2. Detect Fielder Column
    fielder_col = "fielder_id"

    # 3. Standard Catches & Stumpings
    if fielder_col:
        fielder_ids = pd.to_numeric(fielding_dels[fielder_col], errors="coerce")
        catches += int(((fielder_ids == player_id) & (d_kind == "caught")).sum())
        stumpings += int(((fielder_ids == player_id) & (d_kind == "stumped")).sum())

    # 4. Caught & Bowled (where bowler_id == player_id)
    if "bowler_id" in fielding_dels.columns:
        bowler_ids = pd.to_numeric(fielding_dels["bowler_id"], errors="coerce")
        catches += int(
            ((bowler_ids == player_id) & (d_kind == "caught and bowled")).sum()
        )

    return catches, stumpings


def _calc_batting_metrics(
    player_id: int,
    player_dels: pd.DataFrame,
    all_deliveries: pd.DataFrame,
    player_matches: pd.DataFrame,
    matches: pd.DataFrame,
    teams: pd.DataFrame,
    venues: pd.DataFrame,
) -> dict:
    """Calculates all batting and fielding statistics."""
    if player_matches.empty:
        return {}

    total_teams = player_matches["team_id"].nunique()
    total_matches = player_matches["match_id"].nunique()

    # -------------------------------------------------------------------------
    # FIELDING STATS
    # -------------------------------------------------------------------------
    relevant_match_ids = player_matches["match_id"].tolist()
    fielding_dels = (
        all_deliveries[all_deliveries["match_id"].isin(relevant_match_ids)]
        if not all_deliveries.empty
        else pd.DataFrame()
    )

    catches, stumpings = _calc_fielding_stats(player_id, fielding_dels)

    # -------------------------------------------------------------------------
    # BATTING STATS
    # -------------------------------------------------------------------------
    if player_dels.empty:
        return {
            "teams_played": total_teams,
            "matches": total_matches,
            "innings": 0,
            "not_outs": 0,
            "runs": 0,
            "highest_score": "0",
            "average": 0.0,
            "balls_faced": 0,
            "strike_rate": 0.0,
            "hundreds": 0,
            "fifties": 0,
            "fours": 0,
            "sixes": 0,
            "catches": catches,
            "stumpings": stumpings,
            "powerplay_runs": 0,
            "death_runs": 0,
            "best_venue": "N/A",
            "most_runs_vs": "N/A",
            "ducks": 0,
        }

    # Innings Batted
    innings = player_dels["match_id"].nunique()

    # Total Runs
    total_runs = int(player_dels["batsman_runs"].sum())
    
    # Balls Faced (Exclude wide balls)
    if "is_wide" in player_dels.columns:
        # Treats True, 1, or "true" as a wide ball and excludes it
        is_wide_mask = (
            player_dels["is_wide"]
            .fillna(False)
            .astype(str)
            .str.lower()
            .isin(["true", "1", "1.0"])
        )
        valid_balls = player_dels[~is_wide_mask]
    elif "wides" in player_dels.columns:
        # Fallback to 'wides' column if present
        valid_balls = player_dels[player_dels["wides"].fillna(0) == 0]
    else:
        valid_balls = player_dels

    balls_faced = len(valid_balls)

    # Strike Rate
    sr = (total_runs / balls_faced * 100) if balls_faced > 0 else 0.0

    # Boundaries
    fours = int((player_dels["is_four"] ).sum())
    sixes = int((player_dels["is_six"] ).sum())

    # Overs Breakdown
    if "over" in player_dels.columns:
        pp_runs = int(player_dels[player_dels["over"] <= 6]["batsman_runs"].sum())
        death_runs = int(player_dels[player_dels["over"] >= 16]["batsman_runs"].sum())
    else:
        pp_runs = 0
        death_runs = 0

    # Match-by-Match Batting Aggregation
    match_bat = (
        player_dels.groupby("match_id")
        .agg(
            runs=("batsman_runs", "sum"),
            is_out=("is_wicket", lambda x: any(x)),
        )
        .reset_index()
    )

    # Not Outs & Ducks
    outs_count = match_bat["is_out"].sum()
    not_outs = innings - outs_count
    ducks = int(((match_bat["runs"] == 0) & match_bat["is_out"]).sum())

    # Average
    avg = (total_runs / outs_count) if outs_count > 0 else total_runs

    # Hundreds & Fifties
    hundreds = int((match_bat["runs"] >= 100).sum())
    fifties = int(((match_bat["runs"] >= 50) & (match_bat["runs"] < 100)).sum())

    # Highest Score
    max_runs = match_bat["runs"].max() if not match_bat.empty else 0
    max_match_id = (
        match_bat[match_bat["runs"] == max_runs]["match_id"].iloc[0]
        if not match_bat.empty
        else None
    )
    is_not_out = (
        not match_bat[match_bat["match_id"] == max_match_id]["is_out"].iloc[0]
        if max_match_id
        else False
    )
    highest_score_str = f"{max_runs}*" if is_not_out else f"{max_runs}"

    # Most Runs Against Team
    most_runs_vs = "N/A"
    if not match_bat.empty and not matches.empty and not teams.empty:
        match_bat_merged = match_bat.merge(
            player_matches[["match_id", "team1_id", "team2_id", "team_id"]],
            on="match_id",
            how="inner",
        )
        match_bat_merged["opp_id"] = match_bat_merged.apply(
            lambda r: r["team2_id"] if r["team1_id"] == r["team_id"] else r["team1_id"],
            axis=1,
        )
        opp_runs = match_bat_merged.groupby("opp_id")["runs"].sum()
        if not opp_runs.empty:
            top_opp_id = opp_runs.idxmax()
            top_opp_runs = opp_runs.max()
            opp_match = teams[teams["team_id"] == top_opp_id]
            opp_name = (
                opp_match["team_name"].iloc[0]
                if not opp_match.empty
                else f"Team {top_opp_id}"
            )
            most_runs_vs = f"{opp_name} ({top_opp_runs})"

    # Most Successful Venue
    best_venue = "N/A"
    if not match_bat.empty and not matches.empty and not venues.empty:
        venue_col = "venue_id" if "venue_id" in matches.columns else "id"
        match_bat_merged = match_bat.merge(
            matches[["match_id", venue_col]], on="match_id", how="inner"
        )
        venue_runs = match_bat_merged.groupby(venue_col)["runs"].sum()
        if not venue_runs.empty:
            top_venue_id = venue_runs.idxmax()
            top_venue_runs = venue_runs.max()
            venue_id_col = "venue_id" if "venue_id" in venues.columns else "id"
            v_match = venues[venues[venue_id_col] == top_venue_id]
            if not v_match.empty:
                v_name = (
                    v_match["venue_name"].iloc[0]
                    if "venue_name" in v_match.columns
                    else v_match["name"].iloc[0]
                )
                best_venue = f"{v_name} ({top_venue_runs})"

    return {
        "teams_played": total_teams,
        "matches": total_matches,
        "innings": innings,
        "not_outs": not_outs,
        "runs": total_runs,
        "highest_score": highest_score_str,
        "average": round(avg, 2),
        "balls_faced": balls_faced,
        "strike_rate": round(sr, 2),
        "hundreds": hundreds,
        "fifties": fifties,
        "fours": fours,
        "sixes": sixes,
        "catches": catches,
        "stumpings": stumpings,
        "powerplay_runs": pp_runs,
        "death_runs": death_runs,
        "best_venue": best_venue,
        "most_runs_vs": most_runs_vs,
        "ducks": ducks,
    }


def get_player_batting_stats(
    player_id: int,
    deliveries: pd.DataFrame,
    matches: pd.DataFrame,
    teams: pd.DataFrame,
    venues: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generates overall and team-wise batting statistics DataFrames."""
    player_matches = get_player_matches(player_id, matches)
    if player_matches.empty or deliveries.empty:
        return pd.DataFrame(), pd.DataFrame()

    player_dels = deliveries[deliveries["batter_id"] == player_id]

    # Overall Stats
    overall_dict = _calc_batting_metrics(
        player_id, player_dels, deliveries, player_matches, matches, teams, venues
    )
    df_overall = pd.DataFrame([overall_dict])

    # Team-wise Breakdown
    team_rows = []
    for t_id in player_matches["team_id"].unique():
        t_matches = player_matches[player_matches["team_id"] == t_id]
        t_match_ids = t_matches["match_id"].tolist()
        t_dels = player_dels[player_dels["match_id"].isin(t_match_ids)]

        t_stats = _calc_batting_metrics(
            player_id, t_dels, deliveries, t_matches, matches, teams, venues
        )
        team_name = (
            teams[teams["team_id"] == t_id]["team_name"].iloc[0]
            if not teams[teams["team_id"] == t_id].empty
            else f"Team {t_id}"
        )
        t_stats["team_name"] = team_name
        team_rows.append(t_stats)

    df_teams = pd.DataFrame(team_rows)
    if not df_teams.empty:
        cols = ["team_name"] + [c for c in df_teams.columns if c != "team_name"]
        df_teams = df_teams[cols]

    return df_overall, df_teams


def _calc_bowling_metrics(
    player_dels: pd.DataFrame,
    player_matches: pd.DataFrame,
    matches: pd.DataFrame,
    teams: pd.DataFrame,
) -> dict:
    """Calculates all 16 required bowling statistics."""
    if player_matches.empty:
        return {}

    total_teams = player_matches["team_id"].nunique()
    total_matches = player_matches["match_id"].nunique()

    if player_dels.empty:
        return {
            "teams_played": total_teams,
            "matches": total_matches,
            "innings": 0,
            "balls_bowled": 0,
            "runs_conceded": 0,
            "wickets": 0,
            "best_fig_innings": "0/0",
            "best_fig_match": "0/0",
            "average": 0.0,
            "economy": 0.0,
            "strike_rate": 0.0,
            "four_wkt_innings": 0,
            "five_wkt_innings": 0,
            "ten_wkt_innings": 0,
            "best_sr_innings": "N/A",
            "best_econ_innings": "N/A",
        }

    # Innings Bowled
    innings = player_dels["match_id"].nunique()

    # ✅ FIXED: Always create Series for condition checking
    wides_series = (
        player_dels["wides"].fillna(0)
        if "wides" in player_dels.columns
        else pd.Series(0, index=player_dels.index)
    )
    noballs_series = (
        player_dels["noballs"].fillna(0)
        if "noballs" in player_dels.columns
        else pd.Series(0, index=player_dels.index)
    )

    # Valid Balls (Exclude wides and no-balls)
    mask_valid = (wides_series == 0) & (noballs_series == 0)
    valid_balls_df = player_dels[mask_valid]
    balls_bowled = len(valid_balls_df)

    # Runs Conceded
    runs_conceded = (
        int(player_dels["total_runs"].sum())
        if "total_runs" in player_dels.columns
        else int(player_dels["batsman_runs"].sum())
    )

    # Total Wickets (Exclude run outs and retired hurt)
    wicket_mask = (player_dels["is_wicket"] == True) & (
        ~player_dels["wicket_kind"]
        .astype(str)
        .str.lower()
        .isin(["run out", "retired hurt"])
    )
    wickets = int(wicket_mask.sum())

    # Bowling Avg, Economy, SR
    avg = (runs_conceded / wickets) if wickets > 0 else 0.0
    overs = balls_bowled / 6.0
    econ = (runs_conceded / overs) if overs > 0 else 0.0
    sr = (balls_bowled / wickets) if wickets > 0 else 0.0

    # ✅ FIXED: Match Aggregation for Innings Figures & Milestones
    temp_df = player_dels.copy()
    temp_df["is_valid_ball"] = mask_valid
    temp_df["is_legal_wicket"] = wicket_mask

    match_bowl = (
        temp_df.groupby("match_id")
        .agg(
            runs=(
                "total_runs" if "total_runs" in temp_df.columns else "batsman_runs",
                "sum",
            ),
            valid_balls=("is_valid_ball", "sum"),
            wickets=("is_legal_wicket", "sum"),
        )
        .reset_index()
    )

    # Multi-wicket Innings
    four_wkts = int((match_bowl["wickets"] == 4).sum())
    five_wkts = int(((match_bowl["wickets"] >= 5) & (match_bowl["wickets"] < 10)).sum())
    ten_wkts = int((match_bowl["wickets"] >= 10).sum())

    # Best Figures
    if not match_bowl.empty:
        match_bowl_sorted = match_bowl.sort_values(
            by=["wickets", "runs"], ascending=[False, True]
        )
        best_row = match_bowl_sorted.iloc[0]
        best_fig_innings = f"{int(best_row['wickets'])}/{int(best_row['runs'])}"
        best_fig_match = best_fig_innings
    else:
        best_fig_innings = "0/0"
        best_fig_match = "0/0"

    # Best SR & Economy in an Innings (Min 12 valid balls bowled)
    qualified = match_bowl[match_bowl["valid_balls"] >= 12].copy()
    if not qualified.empty:
        qualified["sr"] = qualified.apply(
            lambda r: (r["valid_balls"] / r["wickets"]) if r["wickets"] > 0 else np.inf,
            axis=1,
        )
        qualified["econ"] = qualified["runs"] / (qualified["valid_balls"] / 6.0)

        min_sr = qualified["sr"].min()
        best_sr_innings = f"{round(min_sr, 2)} balls/wkt" if min_sr != np.inf else "N/A"
        best_econ_innings = f"{round(qualified['econ'].min(), 2)} rpo"
    else:
        best_sr_innings = "N/A"
        best_econ_innings = "N/A"

    return {
        "teams_played": total_teams,
        "matches": total_matches,
        "innings": innings,
        "balls_bowled": balls_bowled,
        "runs_conceded": runs_conceded,
        "wickets": wickets,
        "best_fig_innings": best_fig_innings,
        "best_fig_match": best_fig_match,
        "average": round(avg, 2),
        "economy": round(econ, 2),
        "strike_rate": round(sr, 2),
        "four_wkt_innings": four_wkts,
        "five_wkt_innings": five_wkts,
        "ten_wkt_innings": ten_wkts,
        "best_sr_innings": best_sr_innings,
        "best_econ_innings": best_econ_innings,
    }


def get_player_bowling_stats(
    player_id: int,
    deliveries: pd.DataFrame,
    matches: pd.DataFrame,
    teams: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generates overall and team-wise bowling statistics DataFrames."""
    player_matches = get_player_matches(player_id, matches)
    if player_matches.empty or deliveries.empty:
        return pd.DataFrame(), pd.DataFrame()

    player_dels = deliveries[deliveries["bowler_id"] == player_id]

    # Overall Stats
    overall_dict = _calc_bowling_metrics(player_dels, player_matches, matches, teams)
    df_overall = pd.DataFrame([overall_dict])

    # Team-wise Breakdown
    team_rows = []
    for t_id in player_matches["team_id"].unique():
        t_matches = player_matches[player_matches["team_id"] == t_id]
        t_match_ids = t_matches["match_id"].tolist()
        t_dels = player_dels[player_dels["match_id"].isin(t_match_ids)]

        t_stats = _calc_bowling_metrics(t_dels, t_matches, matches, teams)
        team_name = (
            teams[teams["team_id"] == t_id]["team_name"].iloc[0]
            if not teams[teams["team_id"] == t_id].empty
            else f"Team {t_id}"
        )
        t_stats["team_name"] = team_name
        team_rows.append(t_stats)

    df_teams = pd.DataFrame(team_rows)
    if not df_teams.empty:
        cols = ["team_name"] + [c for c in df_teams.columns if c != "team_name"]
        df_teams = df_teams[cols]

    return df_overall, df_teams


def get_player_knockout_stats(
    player_id: int,
    deliveries: pd.DataFrame,
    matches: pd.DataFrame,
    teams: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculates batting and bowling statistics exclusively for Knockout / Playoff matches

    (Finals, Qualifiers, Eliminators, Semi-Finals).
    """
    if matches.empty or deliveries.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Filter Knockout / Playoff matches
    knockout_keywords = ["final", "qualifier", "eliminator", "semi final", "semi-final"]
    pattern = "|".join(knockout_keywords)

    knockout_matches = matches[
        matches["match_title"].astype(str).str.lower().str.contains(pattern, regex=True)
    ]

    if knockout_matches.empty:
        return pd.DataFrame(), pd.DataFrame()

    player_matches = get_player_matches(player_id, knockout_matches)
    if player_matches.empty:
        return pd.DataFrame(), pd.DataFrame()

    ko_match_ids = player_matches["match_id"].tolist()
    ko_dels = deliveries[deliveries["match_id"].isin(ko_match_ids)]

    # Batting Knockout Stats
    bat_dels = ko_dels[ko_dels["batter_id"] == player_id]
    total_runs = int(bat_dels["batsman_runs"].sum()) if not bat_dels.empty else 0
    valid_balls = (
        bat_dels[~bat_dels["wides"].notna() | (bat_dels["wides"] == 0)]
        if "wides" in bat_dels.columns
        else bat_dels
    )
    balls = len(valid_balls) if not bat_dels.empty else 0
    innings = bat_dels["match_id"].nunique() if not bat_dels.empty else 0

    match_bat = (
        (
            bat_dels.groupby("match_id")
            .agg(runs=("batsman_runs", "sum"), is_out=("is_wicket", lambda x: any(x)))
            .reset_index()
        )
        if not bat_dels.empty
        else pd.DataFrame()
    )

    outs = match_bat["is_out"].sum() if not match_bat.empty else 0
    not_outs = innings - outs
    highest = match_bat["runs"].max() if not match_bat.empty else 0
    avg = round(total_runs / outs, 2) if outs > 0 else float(total_runs)
    sr = round(total_runs / balls * 100, 2) if balls > 0 else 0.0
    fifties = (
        int(((match_bat["runs"] >= 50) & (match_bat["runs"] < 100)).sum())
        if not match_bat.empty
        else 0
    )
    hundreds = int((match_bat["runs"] >= 100).sum()) if not match_bat.empty else 0

    df_bat_ko = pd.DataFrame(
        [
            {
                "Matches": player_matches["match_id"].nunique(),
                "Innings": innings,
                "NO": not_outs,
                "Runs": total_runs,
                "HS": highest,
                "Avg": avg,
                "BF": balls,
                "SR": sr,
                "50s": fifties,
                "100s": hundreds,
            }
        ]
    )

    # Bowling Knockout Stats
    bowl_dels = ko_dels[ko_dels["bowler_id"] == player_id]
    b_innings = bowl_dels["match_id"].nunique() if not bowl_dels.empty else 0

    wides_series = (
        bowl_dels["wides"].fillna(0)
        if "wides" in bowl_dels.columns
        else pd.Series(0, index=bowl_dels.index)
    )
    noballs_series = (
        bowl_dels["noballs"].fillna(0)
        if "noballs" in bowl_dels.columns
        else pd.Series(0, index=bowl_dels.index)
    )
    valid_b_df = (
        bowl_dels[(wides_series == 0) & (noballs_series == 0)]
        if not bowl_dels.empty
        else pd.DataFrame()
    )
    balls_bowled = len(valid_b_df)

    runs_conceded = (
        int(bowl_dels["total_runs"].sum())
        if "total_runs" in bowl_dels.columns and not bowl_dels.empty
        else (int(bowl_dels["batsman_runs"].sum()) if not bowl_dels.empty else 0)
    )

    wicket_mask = (
        (bowl_dels["is_wicket"] == True)
        & (
            ~bowl_dels["wicket_kind"]
            .astype(str)
            .str.lower()
            .isin(["run out", "retired hurt"])
        )
        if not bowl_dels.empty
        else pd.Series(False, index=bowl_dels.index)
    )
    wickets = int(wicket_mask.sum())

    b_avg = round(runs_conceded / wickets, 2) if wickets > 0 else 0.0
    overs = balls_bowled / 6.0
    econ = round(runs_conceded / overs, 2) if overs > 0 else 0.0

    df_bowl_ko = pd.DataFrame(
        [
            {
                "Matches": player_matches["match_id"].nunique(),
                "Innings": b_innings,
                "Balls": balls_bowled,
                "Runs": runs_conceded,
                "Wkts": wickets,
                "Avg": b_avg,
                "Econ": econ,
            }
        ]
    )

    return df_bat_ko, df_bowl_ko
