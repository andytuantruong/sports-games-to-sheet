import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def collect_nba_game_data():
    driver = webdriver.Firefox()

    # URL for NBA lineups on Rotowire
    rotowire_url = "https://www.rotowire.com/basketball/nba-lineups.php"
    driver.get(rotowire_url)
    time.sleep(2)  # Allow time for the page to load

    # Xpath for game containers
    game_elements = driver.find_elements(
        By.XPATH,
        "//div[contains(@class, 'lineup is-nba') and "
        "not(contains(@class, 'lineup is-nba is-tools')) and "
        "not(contains(@class, 'is-deposit-offer')) and "
        "not(contains(@class, 'lineup is-nba is-tools is-picks')) and "
        "not(contains(@class, 'lineup-gdc'))]"
    )

    games_array = []  # To store structured game data
    game_index = 1

    for game_element in game_elements:
        try:
            # Extract text from specific classes for away and home teams
            away_team_text = game_element.find_element(By.CLASS_NAME, "lineup__team.is-visit").text
            home_team_text = game_element.find_element(By.CLASS_NAME, "lineup__team.is-home").text

        except Exception as e:
            away_team_text = "N/A"
            home_team_text = "N/A"
            print(f"Error processing game {game_index}: {e}")

        # Store the game data
        game_row = [game_index, away_team_text, home_team_text]
        games_array.append(game_row)

        game_index += 1

    driver.close()
    return games_array

def update_game_results():
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_date = yesterday.strftime('%Y-%m-%d')
    url = f"https://www.rotowire.com/basketball/scoreboard.php?date={yesterday_date}"

    driver = webdriver.Firefox()
    driver.get(url)
    time.sleep(2)

    # Extract game score results
    # .col used for games in OT
    game_elements = driver.find_elements(By.CSS_SELECTOR, ".col-2.align-c.bold, .col.align-c.bold")
    
    game_results = {}

    # Print the number of game elements found
    print(f"Found {len(game_elements)} game elements.")
    
    # Inspect each game_element
    for i, game in enumerate(game_elements):
        print(f"Game {i+1}:")
        
        # Split the text content by the newline character
        try:
            final_game_text = game.text.strip()
            scores = final_game_text.split("\n")  # Split by newline
            
            if len(scores) == 2:
                # Convert away and home scores to integers
                away_score = int(scores[0].strip())
                home_score = int(scores[1].strip())
                
                if away_score > home_score:
                    winner = "AWAY"
                elif home_score >away_score:
                    winner = "HOME"

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
    # Collect the game data as a structured array
    #todays_games = collect_nba_game_data()

    #print("\nGames (AWAY vs HOME):")
    #for game_info in todays_games:
    #    print(f"Game {game_info[0]}: {game_info[1]} vs {game_info[2]}")
    
    gr = update_game_results()
    print(f"gr: {gr}")