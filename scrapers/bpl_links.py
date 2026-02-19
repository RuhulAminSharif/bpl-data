from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
import pandas as pd
import time
import json

def bplEditionLinksScraper(driver, bpl="https://www.espncricinfo.com/records/trophy/team-series-results/bangladesh-premier-league-159" ):
  driver.get(bpl)
  time.sleep(5)

  try:
    wait = WebDriverWait(driver, 20)

    table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.ds-table-auto")))
    tbody = table.find_element(By.TAG_NAME, "tbody")

    rows = tbody.find_elements(By.CSS_SELECTOR, "tbody tr")

    data = []
    cnt = 1
    for row in rows:
      cells = row.find_elements(By.TAG_NAME, "td")
    
      if len(cells) >= 3:
        anchor = cells[0].find_element(By.TAG_NAME, "a")
        series_name = anchor.text
        series_link = anchor.get_attribute("href")
        season = cells[1].text
        winner = cells[2].text
        data.append({
          "Season_ID": cnt,
          "Edition_Name": series_name,
          "Season": season,
          "Winner": winner,
          "Link": series_link
        })
        cnt += 1
    df = pd.DataFrame(data)
    return df
  except Exception as e:
    print(f"Access denied or Page structure changed: {e}")
    driver.save_screenshot("error_check.png")


def matches_links(driver, season_id, start_match_id, bpl_edition_link):
  driver.get(bpl_edition_link)
  matches_container = driver.find_element(By.CSS_SELECTOR, ".ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line.ds-mb-4")
  matches = matches_container.find_elements(By.XPATH, "./div[2]/a")

  data = []
  match_id = start_match_id
  for match in matches:
    url = match.get_attribute("href")
    if url:
      data.append({
        "season_id": season_id,
        "match_id": match_id,
        "match_link": url,
      })
      match_id += 1
  all_matches = pd.DataFrame(data)    
  return all_matches
  
def get_name(obj_list, index=0):
  if obj_list and len(obj_list) > index:
    return obj_list[index].get('player', {}).get('longName')
  return None


def match_info(driver, season_id, match_id, match_url):
  driver.get(match_url)

  try:
    json_text = driver.find_element(By.ID, "__NEXT_DATA__").get_attribute('innerHTML')
    raw_dict = json.loads(json_text)

    app_props = raw_dict.get('props', {}).get('appPageProps', {})
    page_data = app_props.get('data', {})
    core_data = page_data.get('data', {})

    match_data = core_data.get('match')
    content_data = core_data.get('content')

    if not match_data:
      print(f"Match data object not found for ID {match_id}")
      return pd.DataFrame()

    # --- Teams ---
    teams_list = match_data.get('teams', [])
    team_map = {t['team']['id']: t['team']['longName'] for t in teams_list if 'team' in t}

    team1 = teams_list[0]['team']['longName'] if len(teams_list) > 0 else None
    team2 = teams_list[1]['team']['longName'] if len(teams_list) > 1 else None
    team1_id = teams_list[0]['team']['id'] if len(teams_list) > 0 else None
    team2_id = teams_list[1]['team']['id'] if len(teams_list) > 1 else None

    # --- Toss ---
    toss_winner_id = match_data.get('tossWinnerTeamId')
    toss_winner = team_map.get(toss_winner_id)
    # tossWinnerChoice: 1 = Bat, 2 = Bowl
    toss_choice = match_data.get('tossWinnerChoice')
    toss_decision = "Bat" if toss_choice == 1 else "Bowl"

    # --- Innings ---
    innings_list = content_data.get('innings', [])
    inn1 = next((i for i in innings_list if i.get('inningNumber') == 1), {})
    inn2 = next((i for i in innings_list if i.get('inningNumber') == 2), {})

    # team that batted first is the one in inning 1
    first_batting_team_id = inn1.get('team', {}).get('id')
    second_batting_team_id = inn2.get('team', {}).get('id')

    # --- Winner & Result ---
    winner_id = match_data.get('winnerTeamId')
    winner = team_map.get(winner_id)

    status_data = match_data.get('statusData', {}).get('statusTextLangData', {})

    if winner_id is None:
      # No result / tie / abandoned
      res_type = match_data.get('statusText', 'No Result')
      win_margin = None
    elif winner_id == first_batting_team_id:
      # Winner batted first → won by runs
      res_type = "Runs"
      # margin = winner's score - loser's score
      win_margin = inn1.get('runs', 0) - inn2.get('runs', 0)
    else:
      # Winner batted second → won by wickets
      res_type = "Wickets"
      # wickets in hand = 10 - wickets lost in inn2
      win_margin = 10 - inn2.get('wickets', 0)

    # --- Captains & Players ---
    team_players = content_data.get('matchPlayers', {}).get('teamPlayers', [])

    t1_cap, t2_cap = None, None
    t1_players, t2_players = [], []

    for tp in team_players:
      team_id = tp.get('team', {}).get('id')
      players = tp.get('players', [])
      player_names = [p.get('player', {}).get('longName') for p in players]
      captain = next(
          (p.get('player', {}).get('longName') for p in players if p.get('playerRoleType') == 'C'),
          None
      )
      if team_id == team1_id:
        t1_cap = captain
        t1_players = player_names
      elif team_id == team2_id:
        t2_cap = captain
        t2_players = player_names

    # --- Player of Match ---
    awards = content_data.get('matchPlayerAwards', [])
    pom = next(
      (a.get('player', {}).get('longName') for a in awards if a.get('type') == 'PLAYER_OF_MATCH'),
      None
    )

    # --- Match basics ---
    match_date     = match_data.get("startDate")
    match_city     = match_data.get('ground', {}).get('town', {}).get('name')
    match_venue    = match_data.get('ground', {}).get('longName')
    match_floodlit = match_data.get('floodlit')
    match_title    = match_data.get('title')

    row = {
      "season_id":      season_id,
      "match_id":       match_id,
      "date":           match_date,
      "city":           match_city,
      "venue":          match_venue,
      "floodlit":       match_floodlit,
      "match_title":    match_title,
      "team1":          team1,
      "team2":          team2,
      "toss_winner":    toss_winner,
      "toss_decision":  toss_decision,
      "team1_score":    inn1.get('runs'),
      "team1_wickets":  inn1.get('wickets'),
      "team1_overs":    inn1.get('overs'),
      "team2_score":    inn2.get('runs'),
      "team2_wickets":  inn2.get('wickets'),
      "team2_overs":    inn2.get('overs'),
      "team1_captain":  t1_cap,
      "team2_captain":  t2_cap,
      "team1_players":  t1_players,
      "team2_players":  t2_players,
      "winner":         winner,
      "result_type":    res_type,
      "win_margin":     win_margin,
      "player_of_match": pom,
      "umpire1":        get_name(match_data.get('umpires'), 0),
      "umpire2":        get_name(match_data.get('umpires'), 1),
      "tv_umpire":      get_name(match_data.get('tvUmpires'), 0),
      "reserve_umpire": get_name(match_data.get('reserveUmpires'), 0),
      "match_referee":  get_name(match_data.get('matchReferees'), 0),
    }

    return pd.DataFrame([row])

  except Exception as e:
    print(f"CRITICAL Error on match {match_id}: {str(e)}")
    return pd.DataFrame()