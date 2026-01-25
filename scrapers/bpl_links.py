from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
import pandas as pd
import time

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


def matches_links(driver, bpl_edition_link):
  driver.get(bpl_edition_link)
  matches_container = driver.find_element(By.CSS_SELECTOR, ".ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line.ds-mb-4")
  matches = matches_container.find_elements(By.XPATH, "./div[2]/a")

  all_matches = []
  for match in matches:
    url = match.get_attribute("href")
    if url:
      match_info = {
        "match_link": url,
        "edition_url": bpl_edition_link,
      }
      all_matches.append(match_info)
        
  return all_matches