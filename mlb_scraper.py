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
    if specific_date:
        target_date = specific_date
    else:
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime('%Y-%m-%d')
        
    url = f"https://www.rotowire.com/baseball/scoreboard.php?date={target_date}"
    
    driver = setup_ff_driver()
    driver.get(url)
    
    # Give the page time to load
    time.sleep(3)
    
    # Extract game score results - using the same approach as in the NBA scraper
    game_elements = driver.find_elements(By.CSS_SELECTOR, ".col-2.align-c.bold, .col.align-c.bold")
    
    game_results = {}
    
    # Print the number of game elements found
    print(f"Found {len(game_elements)} MLB game elements for date {target_date}.")
    
    # Inspect each game_element
    for i, game in enumerate(game_elements):
        print(f"Game {i+1}:")
        
        try:
            # Split the text content by the newline character
            final_game_text = game.text.strip()
            scores = final_game_text.split("\n")  # Split by newline
            
            if len(scores) == 2:
                # Convert away and home scores to integers
                away_score = int(scores[0].strip())
                home_score = int(scores[1].strip())
                
                if away_score > home_score:
                    winner = "AWAY"
                elif home_score > away_score:
                    winner = "HOME"
                else:
                    winner = "TIE"

                # Store results in dictionary
                game_results[i+1] = {
                    "away_score": away_score,
                    "home_score": home_score,
                    "winner": winner
                }
                
                print(f"Away score: {away_score}, Home score: {home_score}, Winner: {winner}")
            else:
                print(f"Error parsing scores for game {i+1}: {final_game_text}")
        
        except Exception as e:
            print(f"Error while processing game {i+1}: {e}")
        
        print("-" * 50)

    driver.quit()
    return game_results

if __name__ == '__main__':
    print("Testing MLB game data collection...")
    games = collect_mlb_game_data()
    print(f"Collected {len(games)} games")
    