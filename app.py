from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapers.bpl_links import matches_links

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=chrome_options)

bpl_edition_link = "https://www.espncricinfo.com/series/bangladesh-premier-league-2011-12-547342/match-schedule-fixtures-and-results"
lists = matches_links(driver=driver, bpl_edition_link=bpl_edition_link)
for i in lists:
  print(i)
driver.quit()