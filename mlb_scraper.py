import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

def setup_ff_driver():
    """
    Set up and return a Firefox webdriver with headless options.
    
    Returns:
        webdriver.Firefox: Configured Firefox webdriver instance
    """
    firefox_options = Options()
    firefox_options.add_argument('--headless')
    service = Service()
    driver = webdriver.Firefox(options=firefox_options, service=service)
    return driver

def collect_mlb_game_data():
    """
    Scrape MLB game data from Rotowire's daily lineups page.
    
    Returns:
        list: List of game data with format [[game_index, away_team, home_team], ...]
    """
    driver = setup_ff_driver()

    # URL for MLB lineups on Rotowire (for tomorrow's games)
    rotowire_url = "https://www.rotowire.com/baseball/daily-lineups.php"
    driver.get(rotowire_url)
    
    # Give the page time to load
    time.sleep(3)
    
    # Find all game containers
    game_elements = driver.find_elements(
        By.XPATH,
        "//div[contains(@class, 'lineup is-mlb') and "
        "not(contains(@class, 'lineup is-mlb is-tools')) and "
        "not(contains(@class, 'is-deposit-offer')) and "
        "not(contains(@class, 'lineup is-mlb is-tools is-picks')) and "
        "not(contains(@class, 'lineup-gdc'))]"
    )
    
    games_array = []  # To store structured game data
    game_index = 1
    
    print(f"Found {len(game_elements)} MLB games scheduled for tomorrow")
    
    for game_element in game_elements:
        try:
            # Extract text from specific classes for away and home teams
            away_team_text = game_element.find_element(By.CLASS_NAME, "lineup__team.is-visit").text
            home_team_text = game_element.find_element(By.CLASS_NAME, "lineup__team.is-home").text
            
            # Store the game data
            game_row = [game_index, away_team_text, home_team_text]
            games_array.append(game_row)
            
            print(f"Game {game_index}: {away_team_text} @ {home_team_text}")
            game_index += 1
                
        except Exception as e:
            print(f"Error processing game {game_index}: {e}")
            game_index += 1
    
    driver.quit()
    return games_array

def update_game_results(specific_date=None):
    """
    Scrape MLB game results from Rotowire's scoreboard page.
    
    Args:
        specific_date (str, optional): Date in YYYY-MM-DD format. Defaults to yesterday.
        
    Returns:
        dict: Dictionary of game results with format {game_index: {'winner': 'HOME'/'AWAY'}}
    """
    if specific_date:
        target_date = specific_date
    else:
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime('%Y-%m-%d')
        
    url = f"https://www.rotowire.com/baseball/scoreboard.php?day=yesterday"
    
    driver = setup_ff_driver()
    driver.get(url)
    
    # Give the page time to load
    time.sleep(3)
    
    # Find all game containers using the new structure
    game_containers = driver.find_elements(
        By.XPATH,
        "//div[contains(@class, 'col-4') and contains(@class, 'xl-6') and contains(@class, 'md-12')]"
    )
    
    game_results = {}
    
    print(f"Found {len(game_containers)} MLB game elements for date {target_date}.")
    
    for i, container in enumerate(game_containers):
        try:
            # Find score elements with the specific class and style
            score_elements = container.find_elements(
                By.XPATH,
                ".//div[@class='flex-row align-center' and contains(@style, 'justify-content:space-between;height:40px;')]"
            )
            
            if len(score_elements) >= 2:
                # Get the first div number from each score element
                away_score = None
                home_score = None
                
                # First score element should be away team
                if score_elements[0]:
                    first_div = score_elements[0].find_element(By.XPATH, ".//div[1]")
                    away_score_text = first_div.text.strip()
                    if away_score_text.isdigit():
                        away_score = int(away_score_text)
                
                # Second score element should be home team
                if score_elements[1]:
                    first_div = score_elements[1].find_element(By.XPATH, ".//div[1]")
                    home_score_text = first_div.text.strip()
                    if home_score_text.isdigit():
                        home_score = int(home_score_text)
                
                if away_score is not None and home_score is not None:
                    # Determine winner
                    if away_score > home_score:
                        winner = "AWAY"
                    elif home_score > away_score:
                        winner = "HOME"
                    else:
                        print(f"Tie game found for game {i+1} - skipping")
                        continue

                    # Store results in dictionary
                    game_results[i+1] = {
                        "winner": winner
                    }
                    
                    print(f"Game {i+1}: Away {away_score} - Home {home_score} -> Winner: {winner}")
                else:
                    print(f"Game {i+1}: Could not extract valid scores - Away: {away_score}, Home: {home_score}")
            else:
                print(f"Game {i+1}: Not enough score elements found - found {len(score_elements)} score elements (upcoming game)")
                
        except Exception as e:
            print(f"Error while processing game {i+1}: {e}")

    driver.quit()
    return game_results

if __name__ == '__main__':
    print("Testing MLB game data collection...")
    update_game_results()
