from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from scrapers.bpl_links import match_info
from utils.utils import save_to_csv
import os 
import time
import random
import pandas as pd

def setup():
  options = Options()
  options.set_preference("dom.webdriver.enabled", False)
  options.set_preference("useAutomationExtension", False)
  options.set_preference("permissions.default.image", 2)

  driver = webdriver.Firefox(options=options)
  driver.set_page_load_timeout(30)
  return driver

def teardown(driver):
  driver.quit()

def random_delay(min_sec=3, max_sec=7):
  """Human-like random pause between requests."""
  time.sleep(random.uniform(min_sec, max_sec))

def longer_break(min_sec=30, max_sec=60):
  """Occasional longer pause to mimic human behaviour."""
  t = random.uniform(min_sec, max_sec)
  print(f"  [Break] Pausing for {t:.1f}s...")
  time.sleep(t)

def scrape_with_retry(driver, season_id, match_id, match_url, retries=3):
  """Retry a single match up to `retries` times on failure."""
  for attempt in range(1, retries + 1):
    try:
      result = match_info(driver, season_id, match_id, match_url)
      if not result.empty:
        return result
      else:
        print(f"  [Attempt {attempt}] Empty result for match {match_id}, retrying...")
    except Exception as e:
      print(f"  [Attempt {attempt}] Error on match {match_id}: {e}")
    # Back-off delay before retry
    time.sleep(random.uniform(10, 20) * attempt)
  print(f"  [FAILED] Giving up on match {match_id} after {retries} attempts.")
  return pd.DataFrame()

# ── Checkpoint helpers ─────────────────────────────────────────────────────────

CHECKPOINT_FILE = "data/matches_checkpoint.csv"
OUTPUT_FILE     = "data/matches.csv"
FAILED_FILE     = "data/matches_failed.txt"

def load_checkpoint():
  """Return set of already-scraped match_ids."""
  if os.path.exists(CHECKPOINT_FILE):
    cp = pd.read_csv(CHECKPOINT_FILE)
    return set(cp['match_id'].tolist())
  return set()

def save_checkpoint(row_df):
  """Append a single match row to the checkpoint file."""
  write_header = not os.path.exists(CHECKPOINT_FILE)
  row_df.to_csv(CHECKPOINT_FILE, mode='a', header=write_header, index=False)

def log_failed(match_id):
  with open(FAILED_FILE, 'a') as f:
    f.write(f"{match_id}\n")

# ── Main ───────────────────────────────────────────────────────────────────────

driver = setup()

try:
  df = pd.read_csv("data/matches_list.csv")
  total = len(df)

  # Resume from where we left off
  done_ids = load_checkpoint()
  pending = df[~df['match_id'].isin(done_ids)].reset_index(drop=True)
  print(f"Total: {total} | Already done: {len(done_ids)} | Remaining: {len(pending)}")

  for idx, row in pending.iterrows():
    season_id = row['season_id']
    match_id  = row['match_id']
    match_url = row['match_link']

    print(f"[{idx + 1}/{len(pending)}] Scraping match {match_id} (season {season_id})...")

    curr_df = scrape_with_retry(driver, season_id, match_id, match_url)

    if not curr_df.empty:
      save_checkpoint(curr_df)
      print(f"  ✓ Saved match {match_id}")
    else:
      log_failed(match_id)
      print(f"  ✗ Failed match {match_id} — logged to {FAILED_FILE}")

    random_delay(3, 8)

    if (idx + 1) % 20 == 0:
      longer_break(45, 90)

  # ── Consolidate checkpoint into final output ────────────────────────────────
  if os.path.exists(CHECKPOINT_FILE):
    final_df = pd.read_csv(CHECKPOINT_FILE)
    save_to_csv("data", "matches.csv", final_df)
    print(f"\nDone! {len(final_df)} matches saved to {OUTPUT_FILE}")
  else:
    print("No data was collected.")
  
finally:
  teardown(driver=driver)