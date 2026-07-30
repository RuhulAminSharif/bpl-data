import os
import pandas as pd
import logging

# Configure basic logging to track successful loads and errors
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_data() -> dict:
    """
    Loads BPL CSV data files from the data directory into a dictionary of DataFrames.
    """
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    file_names = [
        "matches.csv",
        "matches_list.csv",
        "match_referees.csv",
        "venues.csv",
        "tv_umpire.csv",
        "players.csv",
        "bpl_history.csv",
        "teams.csv",
        "umpires.csv",
        "reserve_umpires.csv",
    ]

    data_dict = {}

    for file_name in file_names:
        file_path = os.path.join(base_path, file_name)

        # Dynamically create the dictionary key by stripping the '.csv' extension
        # e.g., "matches.csv" becomes "matches"
        dict_key = os.path.splitext(file_name)[0]

        if not os.path.exists(file_path):
            logging.warning(f"File not found: {file_path}")
            data_dict[dict_key] = None  # Or use pd.DataFrame() for an empty fallback
            continue

        try:
            data_dict[dict_key] = pd.read_csv(file_path)
            logging.info(f"Successfully loaded {file_name}")

        except pd.errors.EmptyDataError:
            logging.error(f"File is empty: {file_path}")
            data_dict[dict_key] = None

        except Exception as e:
            logging.error(f"Unexpected error loading {file_name}: {e}")
            data_dict[dict_key] = None

    return data_dict

