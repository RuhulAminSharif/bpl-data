import functools
import os
import sys
import pandas as pd
import re

# Set the root project directory in system path
current_dir = os.getcwd()
sys.path.append(current_dir)


def standardize_match_title(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes casing and standardizes playoff match titles across all seasons."""
    if "match_title" not in df.columns:
        return df

    df["match_title"] = df["match_title"].astype(str).str.strip().str.title()
    df["match_title"] = df["match_title"].apply(
        lambda x: re.sub(
            r"(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), x
        )
    )

    playoff_mapping = {
        "1st Semi-Final": "Eliminator",
        "2nd Semi-Final": "Qualifier 2",
        "Semi-Final": "Eliminator",
        "Elimination Final": "Eliminator",
        "Race To The Final": "Qualifier 2",
        "1st Qualifier": "Qualifier 1",
        "2nd Qualifier": "Qualifier 2",
    }

    # Apply playoff mapping
    df["match_title"] = df["match_title"].replace(playoff_mapping)

    return df


def int_col_conversion(df: pd.DataFrame, int_cols: list) -> pd.DataFrame:
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def float_col_conversion(df: pd.DataFrame, float_cols: list) -> pd.DataFrame:
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    return df


def str_col_conversion(df: pd.DataFrame, str_cols: list) -> pd.DataFrame:
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df


def _load_csv_safely(file_name: str) -> pd.DataFrame:
    """Helper function to load CSV files safely with error handling."""
    path = os.path.join("data", file_name)
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


@functools.cache
def bpl_history_data() -> pd.DataFrame:
    """Reads and cleans BPL History data from data/bpl_history.csv."""
    df = _load_csv_safely("bpl_history.csv")
    if df.empty:
        return df

    int_cols = ["Season_ID"]
    str_cols = ["Edition_Name", "Season", "Winner", "Link"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df


@functools.cache
def matches_list_data() -> pd.DataFrame:
    """Reads and cleans Matches List data from data/matches_list.csv."""
    df = _load_csv_safely("matches_list.csv")
    if df.empty:
        return df

    int_cols = ["Season_ID", "Match_ID"]
    str_cols = ["Series_Slug", "Match_Slug", "Match_Link"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df


@functools.cache
def matches_data() -> pd.DataFrame:
    """Reads and manually casts columns in Matches data from data/matches.csv."""
    df = _load_csv_safely("matches.csv")
    if df.empty:
        return df

    # 1. Date Conversion
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 2. Integer / ID Column Conversions (Nullable Int64 handles NaNs)
    int_cols = [
        "season_id",
        "match_id",
        "venue_id",
        "team1_id",
        "team2_id",
        "team1_captain_id",
        "team2_captain_id",
        "toss_winner_team_id",
        "team1_score",
        "team1_wickets",
        "team2_score",
        "team2_wickets",
        "match_winner_team_id",
        "win_margin",
        "player_of_match_id",
        "umpire1_id",
        "umpire2_id",
        "tv_umpire_id",
        "reserve_umpire_id",
        "match_referee_id",
    ]
    df = int_col_conversion(df, int_cols)

    # 3. Float Conversions (Overs naturally have decimals like 19.4)
    float_cols = ["team1_overs", "team2_overs"]
    df = float_col_conversion(df, float_cols)

    # 4. String Conversions
    str_cols = [
        "city",
        "floodlit",
        "match_title",
        "team1_player_ids",
        "team2_player_ids",
        "toss_decision",
        "result_type",
    ]
    df = str_col_conversion(df, str_cols)
    df = standardize_match_title(df=df)

    return df


@functools.cache
def teams_data() -> pd.DataFrame:
    """Reads and cleans Teams data from data/teams.csv."""
    df = _load_csv_safely("teams.csv")
    if df.empty:
        return df

    int_cols = ["team_id"]
    str_cols = ["team_name"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df


@functools.cache
def players_data() -> pd.DataFrame:
    """Reads and cleans Players data from data/players.csv."""
    df = _load_csv_safely("players.csv")
    if df.empty:
        return df

    int_cols = ["player_id"]
    str_cols = ["player_name"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df


@functools.cache
def venues_data() -> pd.DataFrame:
    """Reads and cleans Venues data from data/venues.csv."""
    df = _load_csv_safely("venues.csv")
    if df.empty:
        return df

    int_cols = ["id"]
    str_cols = ["name", "smallName", "location", "town", "country"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df


@functools.cache
def umpires_data() -> pd.DataFrame:
    """Reads and cleans Umpires data from data/umpires.csv."""
    df = _load_csv_safely("umpires.csv")
    if df.empty:
        return df

    int_cols = ["umpire_id"]
    str_cols = ["umpire_name"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df


@functools.cache
def reserve_umpires_data() -> pd.DataFrame:
    """Reads and cleans Reserve Umpires data from data/reserve_umpires.csv."""
    df = _load_csv_safely("reserve_umpires.csv")
    if df.empty:
        return df

    int_cols = ["reserve_umpire_id"]
    str_cols = ["reserve_umpire_name"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df


@functools.cache
def tv_umpire_data() -> pd.DataFrame:
    """Reads and cleans TV Umpire data from data/tv_umpire.csv."""
    df = _load_csv_safely("tv_umpire.csv")
    if df.empty:
        return df

    int_cols = ["tv_umpire_id"]
    str_cols = ["tv_umpire_name"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df


@functools.cache
def match_referees_data() -> pd.DataFrame:
    """Reads and cleans Match Referees data from data/match_referees.csv."""
    df = _load_csv_safely("match_referees.csv")
    if df.empty:
        return df

    int_cols = ["match_referee_id"]
    str_cols = ["match_referee_data_name"]

    df = int_col_conversion(df, int_cols)
    df = str_col_conversion(df, str_cols)

    return df
