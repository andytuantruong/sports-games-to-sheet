import time
from selenium import webdriver
from selenium.webdriver.common.by import By

def collect_nba_game_data():
    driver = webdriver.Firefox()

    # URL for NBA lineups on Rotowire
    rotowire_url = "https://www.rotowire.com/basketball/nba-lineups.php"
    driver.get(rotowire_url)
    time.sleep(1)

    # Xpath for NBA lineups
    game_elements = driver.find_elements(
        By.XPATH, 
        "//div[contains(@class, 'lineup is-nba') and "
        "not(contains(@class, 'lineup is-nba is-tools')) and "
        "not(contains(@class, 'is-deposit-offer')) and "
        "not(contains(@class, 'lineup is-nba is-tools is-picks')) and "
        "not(contains(@class, 'lineup-gdc'))]"
    )

    # Initialize the array for storing data in array format
    games_array = []
    game_index = 1
    for game_element in game_elements:
        lines = game_element.text.split('\n')
        
        away_team_abbrev = lines[3] if len(lines) > 3 else "N/A"
        home_team_abbrev = lines[4] if len(lines) > 4 else "N/A"
        
        # Store in games_array directly
        game_row = [game_index, away_team_abbrev, home_team_abbrev]
        games_array.append(game_row)
        
        print("Game", game_index)
        print("Away Team Abbreviation:", away_team_abbrev)
        print("Home Team Abbreviation:", home_team_abbrev)
        print()
        
        game_index += 1
    
    driver.close()
    return games_array

if __name__ == '__main__':
    # Collect the game data as a structured array
    todays_games = collect_nba_game_data()
    
    print("\nGames (AWAY vs HOME):")
    for game_info in todays_games:
        print(f"Game {game_info[0]}: {game_info[1]} vs {game_info[2]}")