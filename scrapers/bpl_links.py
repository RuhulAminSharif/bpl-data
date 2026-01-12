from selenium.webdriver.common.by import By 

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