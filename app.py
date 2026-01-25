from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from scrapers.bpl_links import bplEditionLinksScraper
import os 
import pandas as pd

def setup():
  options = Options()
  options.set_preference("dom.webdriver.enabled", False)
  options.set_preference("useAutomationExtension", False)

  driver = webdriver.Firefox(options=options)
  return driver

def teardown(driver):
  driver.quit()

driver = setup()

try:
  df = pd.read_csv("data/bpl_history.csv")
  print(df.info())
finally:
  teardown(driver=driver)