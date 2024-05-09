import requests
import time
import os

from selenium import webdriver
from selenium.webdriver.common.by import By


driver = webdriver.Firefox()

rotowire_url = "https://www.rotowire.com/baseball/daily-lineups.php"
driver.get(rotowire_url)
time.sleep(1)

game_elements = driver.find_elements(
    By.XPATH, 
    "//div[contains(@class, 'lineup is-mlb') "
    "and not(@class='lineup is-mlb is-tools') "
    "and not(@class='lineup is-mlb is-tools is-deposit-offer') "
    "and not (@class='lineup is-ad hide-until-lg')]"
)

# Print full list of info from each game box
for index, game_element in enumerate(game_elements, start=1):
    print("Game Element", index)
    print("Tag Name:", game_element.tag_name)
    print("Text Content:", game_element.text)
    print("Class:", game_element.get_attribute('class'))
    print("-" * 100)

game_index = 1
for game_element in game_elements:
    lines = game_element.text.split('\n')

    away_team_abbrev = lines[3]
    home_team_abbrev = lines[4]

    print("Game", game_index)
    print("Away Team Abbreviation:", away_team_abbrev)
    print("Home Team Abbreviation:", home_team_abbrev)
    print()

    game_index += 1

driver.close()