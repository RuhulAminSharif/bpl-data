import os
from typing import Tuple, cast
import pandas as pd
from cricdata import CricinfoClient

from utils.utils import extract_series_slug
from scrapers.parsers import collect_full_match_data, parse_deliveries


def fetch_matches_by_series(
    ci: CricinfoClient, season_id: int, series_slug: str, start_match_id: int
) -> Tuple[list, int]:
    """
    Fetch match data for a given series slug and format it into a list of dicts.
    Returns the list of match records and the updated Match_ID counter.
    """
    fixtures = ci.series_matches(series_slug)
    matches = fixtures["content"]["matches"]

    series_match_data = []
    current_match_id = start_match_id

    for m in matches:
        match_slug = f"{m['slug']}-{m['objectId']}"
        print(f"Processing: {series_slug} -> {match_slug}")

        series_match_data.append(
            {
                "Season_ID": season_id,
                "Match_ID": current_match_id,
                "Series_Slug": series_slug,
                "Match_Slug": match_slug,
                "Match_Link": f"https://www.espncricinfo.com/series/{series_slug}/{match_slug}/live-cricket-score",
            }
        )
        current_match_id += 1

    return series_match_data, current_match_id


def process_bpl_history(file_path: str, ci: CricinfoClient) -> pd.DataFrame:
    """Read BPL history data, fetch match metadata, and return a consolidated DataFrame."""
    bpl_history = pd.read_csv(file_path)
    all_matches = []
    match_id_counter = 1

    for row in bpl_history.itertuples(index=False):
        series_slug = extract_series_slug(str(row.Link))

        # Fetch matches and update the running Match_ID counter
        matches_data, match_id_counter = fetch_matches_by_series(
            ci=ci,
            season_id=row.Season_ID,
            series_slug=series_slug,
            start_match_id=match_id_counter,
        )
        all_matches.extend(matches_data)

    return pd.DataFrame(all_matches)


def collect_match_details(ci: CricinfoClient, matches_list: pd.DataFrame) -> tuple[
    list[pd.DataFrame],
    list[pd.DataFrame],
    list[pd.DataFrame],
    list[pd.DataFrame],
    list[pd.DataFrame],
    list[pd.DataFrame],
    list[pd.DataFrame],
    list[pd.DataFrame],
]:
    """
    Given a DataFrame of matches, fetch detailed match information for each match.
    Returns tuples of DataFrames with the detailed match data.
    """
    (
        matches,
        teams,
        venues,
        players,
        umpires,
        tv_umpire,
        reserve_umpire,
        match_referee,
    ) = ([], [], [], [], [], [], [], [])

    for row in matches_list.itertuples(index=False):
        Season_ID = row.Season_ID
        Match_ID = row.Match_ID
        Series_Slug = row.Series_Slug
        Match_Slug = row.Match_Slug
        print("Processing =>", Match_ID)
        if Match_ID == 317 or Match_ID == 318:
            continue
        core_data = ci.match_scorecard(str(Series_Slug), str(Match_Slug))
        (
            match_data,
            team_data,
            venue_data,
            players_data,
            umpires_data,
            tv_umpire_data,
            reserve_umpire_data,
            match_referee_data,
        ) = collect_full_match_data(
            core_data=cast(dict, core_data),
            season_id=int(str(Season_ID)),
            match_id=int(str(Match_ID)),
        )
        matches.append(match_data)
        teams.append(team_data)
        venues.append(venue_data)
        players.append(players_data)
        umpires.append(umpires_data)
        tv_umpire.append(tv_umpire_data)
        reserve_umpire.append(reserve_umpire_data)
        match_referee.append(match_referee_data)

    return (
        matches,
        teams,
        venues,
        players,
        umpires,
        tv_umpire,
        reserve_umpire,
        match_referee,
    )


def collect_match_deliveries(ci: CricinfoClient, matches_list: pd.DataFrame):

    deliveries = []
    for row in matches_list.itertuples(index=False):
        Season_ID = row.Season_ID
        Match_ID = row.Match_ID
        Series_Slug = row.Series_Slug
        Match_Slug = row.Match_Slug
        print("Processing =>", Match_ID)
        if Match_ID == 317 or Match_ID == 318:
            continue
        ballItems = ci.match_ball_by_ball(str(Series_Slug), str(Match_Slug))
        delivery_data = parse_deliveries(ballItems=ballItems)
        deliveries.append(delivery_data)
        break
    return deliveries


if __name__ == "__main__":
    DATA_DIR = "./data"
    os.makedirs(DATA_DIR, exist_ok=True)

    client = CricinfoClient()

    matches_list_path = os.path.join(DATA_DIR, "matches_list.csv")
    if not os.path.exists(matches_list_path):
        matches_list = process_bpl_history(
            os.path.join(DATA_DIR, "bpl_history.csv"), ci=client
        )
        matches_list.to_csv(matches_list_path, index=False)
    else:
        matches_list = pd.read_csv(matches_list_path)

    (
        matches,
        teams,
        venues,
        players,
        umpires,
        tv_umpire,
        reserve_umpire,
        match_referee,
    ) = collect_match_details(ci=client, matches_list=matches_list)

    deliveries = collect_match_deliveries(ci=client, matches_list=matches_list)

    pd.concat(matches, ignore_index=True).to_csv(
        os.path.join(DATA_DIR, "matches.csv"), index=False
    )
    pd.concat(teams, ignore_index=True).drop_duplicates(subset=["team_id"]).to_csv(
        os.path.join(DATA_DIR, "teams.csv"), index=False
    )
    pd.concat(venues, ignore_index=True).drop_duplicates(subset=["id"]).to_csv(
        os.path.join(DATA_DIR, "venues.csv"), index=False
    )
    pd.concat(players, ignore_index=True).drop_duplicates(subset=["player_id"]).to_csv(
        os.path.join(DATA_DIR, "players.csv"), index=False
    )
    pd.concat(umpires, ignore_index=True).drop_duplicates(subset=["umpire_id"]).to_csv(
        os.path.join(DATA_DIR, "umpires.csv"), index=False
    )
    pd.concat(tv_umpire, ignore_index=True).drop_duplicates(
        subset=["tv_umpire_id"]
    ).to_csv(os.path.join(DATA_DIR, "tv_umpire.csv"), index=False)
    pd.concat(reserve_umpire, ignore_index=True).drop_duplicates(
        subset=["reserve_umpire_id"]
    ).to_csv(os.path.join(DATA_DIR, "reserve_umpires.csv"), index=False)
    pd.concat(match_referee, ignore_index=True).drop_duplicates(
        subset=["match_referee_id"]
    ).to_csv(os.path.join(DATA_DIR, "match_referees.csv"), index=False)

    pd.concat(deliveries, ignore_index=True).to_csv(
        os.path.join(DATA_DIR, "deliveries.csv"), index=False
    )
