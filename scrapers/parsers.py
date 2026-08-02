import pandas as pd
from typing import Dict, List, Tuple, Any


def _safe_get_list(data: list, index: int, default: dict | None = None):
    """Safely fetch an item from a list or return a default dictionary."""
    if default is None:
        default = {}
    return data[index] if data and len(data) > index else default


def parse_teams(match_data: dict) -> Tuple[Dict, Dict]:
    """Extracts team IDs, names, and captains."""
    teams_list = match_data.get("teams", [])

    t1_raw = _safe_get_list(teams_list, 0)
    t2_raw = _safe_get_list(teams_list, 1)

    team1 = {
        "id": t1_raw.get("team", {}).get("id") if t1_raw.get("team") else None,
        "name": t1_raw.get("team", {}).get("longName") if t1_raw.get("team") else None,
        "captain_id": (
            t1_raw.get("captain", {}).get("objectId") if t1_raw.get("captain") else None
        ),
    }
    team2 = {
        "id": t2_raw.get("team", {}).get("id") if t2_raw.get("team") else None,
        "name": t2_raw.get("team", {}).get("longName") if t2_raw.get("team") else None,
        "captain_id": (
            t2_raw.get("captain", {}).get("objectId") if t2_raw.get("captain") else None
        ),
    }
    return team1, team2


def parse_players(
    content_data: dict, team1_id: int, team2_id: int
) -> Tuple[List, List, List]:
    """Extracts all players and splits them by team."""
    team_players = content_data.get("matchPlayers", {}).get("teamPlayers", [])

    t1_players, t2_players = [], []
    t1_player_ids, t2_player_ids = [], []

    for tp in team_players:
        team_id = tp.get("team", {}).get("id")
        players = tp.get("players", [])
        players_info = [
            {
                "player_id": p.get("player", {}).get("objectId"),
                "player_name": p.get("player", {}).get("longName"),
                "countryId": p.get("player", {}).get("countryTeamId"),
            }
            for p in players
        ]

        if team_id == team1_id:
            t1_players = players_info
            t1_player_ids = [p["player_id"] for p in players_info]
        elif team_id == team2_id:
            t2_players = players_info
            t2_player_ids = [p["player_id"] for p in players_info]

    return t1_players + t2_players, t1_player_ids, t2_player_ids


def parse_venue(match_data: dict) -> Dict:
    """Extracts venue and ground information."""
    ground = match_data.get("ground", {})
    return {
        "id": ground.get("objectId"),
        "name": ground.get("name"),
        "smallName": ground.get("smallName"),
        "location": ground.get("location"),
        "town": ground.get("town", {}).get("name"),
        "country": ground.get("country", {}).get("name"),
    }


def parse_officials(
    match_data: dict,
) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], Dict]:
    """Extracts umpires, TV umpires, and match referees safely."""
    umpires = match_data.get("umpires", [])
    tv_umpires = match_data.get("tvUmpires", [])
    reserve_umpires = match_data.get("reserveUmpires", [])
    match_referee = match_data.get("matchReferees", [])

    u1 = _safe_get_list(umpires, 0).get("player", {})
    u2 = _safe_get_list(umpires, 1).get("player", {})
    tv = _safe_get_list(tv_umpires, 0).get("player", {})
    rv = _safe_get_list(reserve_umpires, 0).get("player", {})
    mr = _safe_get_list(match_referee, 0).get("player", {})

    umpires_data, tv_umpire_data, reserve_umpire_data, match_referee_data = (
        [],
        [],
        [],
        [],
    )
    if u1.get("objectId"):
        umpires_data.append(
            {"umpire_id": u1.get("objectId"), "umpire_name": u1.get("longName")}
        )
    if u2.get("objectId"):
        umpires_data.append(
            {"umpire_id": u2.get("objectId"), "umpire_name": u2.get("longName")}
        )
    if tv.get("objectId"):
        tv_umpire_data.append(
            {"tv_umpire_id": tv.get("objectId"), "tv_umpire_name": tv.get("longName")}
        )
    if rv.get("objectId"):
        reserve_umpire_data.append(
            {
                "reserve_umpire_id": rv.get("objectId"),
                "reserve_umpire_name": rv.get("longName"),
            }
        )

    if mr.get("objectId"):
        match_referee_data.append(
            {
                "match_referee_id": mr.get("objectId"),
                "match_referee_data_name": mr.get("longName"),
            }
        )

    officials_ids = {
        "umpire1_id": u1.get("objectId"),
        "umpire2_id": u2.get("objectId"),
        "tv_umpire_id": tv.get("objectId"),
        "reserve_umpire_id": rv.get("objectId"),
        "match_referee_id": mr.get("objectId"),
    }

    return (
        umpires_data,
        tv_umpire_data,
        reserve_umpire_data,
        match_referee_data,
        officials_ids,
    )


def parse_innings_and_results(
    match_data: dict, content_data: dict, team1_id: int
) -> Dict:
    """Extracts innings scores, toss, and match results."""
    # Toss
    toss_winner_team_id = match_data.get("tossWinnerTeamId")
    toss_choice = match_data.get("tossWinnerChoice")
    toss_decision = (
        "Bat" if toss_choice == 1 else "Bowl"
    )  # tossWinnerChoice: 1 = Bat, 2 = Bowl

    # Innings
    innings_list = content_data.get("innings", [])
    inn1 = next((i for i in innings_list if i.get("inningNumber") == 1), {})
    inn2 = next((i for i in innings_list if i.get("inningNumber") == 2), {})

    # Results
    match_winner_team_id = match_data.get("winnerTeamId")
    if match_winner_team_id is None:
        # No result / tie / abandoned
        res_type = match_data.get("statusText", "No Result")
        win_margin = None
    elif match_winner_team_id == team1_id:
        # Winner batted first → won by runs
        res_type = "Runs"
        # margin = winner's score - loser's score
        win_margin = inn1.get("runs", 0) - inn2.get("runs", 0)
    else:
        # Winner batted second → won by wickets
        res_type = "Wickets"
        # wickets in hand = 10 - wickets lost in inn2
        win_margin = 10 - inn2.get("wickets", 0)

    # Player of Match
    awards = content_data.get("matchPlayerAwards", [])
    pom = next(
        (
            a.get("player", {}).get("objectId")
            for a in awards
            if a.get("type") == "PLAYER_OF_MATCH"
        ),
        None,
    )

    return {
        "toss_winner_team_id": toss_winner_team_id,
        "toss_decision": toss_decision,
        "team1_score": inn1.get("runs"),
        "team1_wickets": inn1.get("wickets"),
        "team1_overs": inn1.get("overs"),
        "team2_score": inn2.get("runs"),
        "team2_wickets": inn2.get("wickets"),
        "team2_overs": inn2.get("overs"),
        "match_winner_team_id": match_winner_team_id,
        "result_type": res_type,
        "win_margin": win_margin,
        "player_of_match_id": pom,
    }


def collect_full_match_data(core_data: dict, season_id: int, match_id: int) -> Tuple:
    """Orchestrates parsing of raw API match data into relational DataFrames."""
    match_data = core_data.get("match", {})
    content_data = core_data.get("content", {})

    # --- Teams and  Players ---
    team1, team2 = parse_teams(match_data)
    players_data, t1_player_ids, t2_player_ids = parse_players(
        content_data, team1["id"], team2["id"]
    )
    # --- Venue Information
    venue_info = parse_venue(match_data)
    # --- Umpires, tvUmpires, reserveUmpires, matchReferees ---
    (
        umpires_data,
        tv_umpire_data,
        reserve_umpire_data,
        match_referee_data,
        officials_ids,
    ) = parse_officials(match_data)

    # --- Innings and Results ---
    result_info = parse_innings_and_results(match_data, content_data, team1["id"])

    # Compile Match Record
    match_record = {
        "season_id": season_id,
        "match_id": match_id,
        "date": match_data.get("startTime"),
        "city": venue_info.get("town"),
        "venue_id": venue_info.get("id"),
        "floodlit": match_data.get("floodlit"),
        "match_title": match_data.get("title"),
        "team1_id": team1["id"],
        "team2_id": team2["id"],
        "team1_captain_id": team1["captain_id"],
        "team2_captain_id": team2["captain_id"],
        "team1_player_ids": t1_player_ids,
        "team2_player_ids": t2_player_ids,
        **result_info,
        **officials_ids,
    }

    team_records = [
        {"team_id": team1["id"], "team_name": team1["name"]},
        {"team_id": team2["id"], "team_name": team2["name"]},
    ]

    return (
        pd.DataFrame([match_record]),
        pd.DataFrame(team_records),
        pd.DataFrame([venue_info]),
        pd.DataFrame(players_data),
        pd.DataFrame(umpires_data),
        pd.DataFrame(tv_umpire_data),
        pd.DataFrame(reserve_umpire_data),
        pd.DataFrame(match_referee_data),
    )


def parse_deliveries(ballItems: list) -> pd.DataFrame:
    parsed_deliveries = []

    if not ballItems:
        return pd.DataFrame()

    for inningsBalls in ballItems:
        if not isinstance(inningsBalls, list):
            continue

        for oneBall in inningsBalls:
            if not isinstance(oneBall, dict):
                continue

            dismissal_info = oneBall.get("dismissal") or {}
            is_wicket = bool(dismissal_info.get("dismissal"))

            wicket_kind = None
            player_out_id = None
            fielder_id = None
            is_keeper = None

            if is_wicket:
                wicket_kind = dismissal_info.get("type")
                player_out_id = (
                    dismissal_info.get("batsman", {}).get("athlete", {}).get("id")
                )

                if wicket_kind not in ["bowled", "lbw"]:
                    fielder_info = dismissal_info.get("fielder", {})
                    fielder_id = fielder_info.get("athlete", {}).get("id")
                    is_keeper = fielder_info.get("isKeeper")

            play_type = oneBall.get("playType", {}).get("id", 0)
            score_value = oneBall.get("scoreValue", 0)

            is_four = False
            is_six = False
            is_wide = False
            is_no_ball = False
            is_bye = False
            is_leg_bye = False

            # Default run allocations
            batsman_runs = 0
            extras_runs = 0

            if play_type == 1:  # Running between wickets
                batsman_runs = score_value

            elif play_type == 2:  # Dot ball
                batsman_runs = 0

            elif play_type == 3:  # Boundary 4
                is_four = True
                batsman_runs = 4

            elif play_type == 4:  # Boundary 6
                is_six = True
                batsman_runs = 6

            elif play_type == 5:  # No Ball
                is_no_ball = True
                # Score value includes the 1-run penalty + batsman runs
                extras_runs = 1
                batsman_runs = max(0, score_value - 1)

            elif play_type == 6:  # Wide
                is_wide = True
                extras_runs = score_value
                batsman_runs = 0

            elif play_type == 7:  # Bye
                is_bye = True
                extras_runs = score_value
                batsman_runs = 0

            elif play_type == 8:  # Leg Bye
                is_leg_bye = True
                extras_runs = score_value
                batsman_runs = 0

            elif play_type == 9:  # Wicket / Out (non-runs)
                batsman_runs = 0

            # Bowler runs = score_value except for Byes and Leg Byes
            bowler_runs = 0 if (is_bye or is_leg_bye) else score_value
            is_extra = is_wide or is_no_ball or is_bye or is_leg_bye

            # -----------------------------------------------------------------
            # 3. CONSTRUCT RECORD
            # -----------------------------------------------------------------
            parsed_deliveries.append(
                {
                    "innings": oneBall.get("period", 0),
                    "over": oneBall.get("over", {}).get("number", 0),
                    "ball": oneBall.get("over", {}).get("ball", 0),
                    "actual_ball": oneBall.get("over", {}).get("actual", 0),
                    "batter_id": oneBall.get("batsman", {})
                    .get("athlete", {})
                    .get("id"),
                    "bowler_id": oneBall.get("bowler", {}).get("athlete", {}).get("id"),
                    "play_type": play_type,
                    "score_value": score_value,
                    "batsman_runs": batsman_runs,
                    "bowler_runs": bowler_runs,
                    "extras_runs": extras_runs,
                    "total_runs": score_value,
                    "is_four": is_four,
                    "is_six": is_six,
                    "is_extra": is_extra,
                    "is_wide": is_wide,
                    "is_no_ball": is_no_ball,
                    "is_bye": is_bye,
                    "is_leg_bye": is_leg_bye,
                    "is_wicket": is_wicket,
                    "wicket_kind": wicket_kind,
                    "player_out_id": player_out_id,
                    "fielder_id": fielder_id,
                    "is_keeper": is_keeper,
                }
            )

    df = pd.DataFrame(parsed_deliveries)

    if df.empty:
        return df

    id_cols = ["batter_id", "bowler_id", "player_out_id", "fielder_id"]
    for col in id_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    return df
