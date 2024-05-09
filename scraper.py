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
    "and not(@class='lineup is-mlb is-tools is-deposit-offer')]"
)

away_team = driver.find_element(By.XPATH,"/html/body/div/div/main/div[3]/div[1]/div[2]/div[1]/div/div[1]/div")
home_team = driver.find_element(By.XPATH,"/html/body/div/div/main/div[3]/div[1]/div[2]/div[1]/div/div[2]/div")

print("Away Team:", away_team.text)
print("Home Team:", home_team.text)
print("Games played today:", len(game_elements))
driver.quit()