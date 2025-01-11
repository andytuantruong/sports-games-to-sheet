import time
from selenium import webdriver
from selenium.webdriver.common.by import By

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

if __name__ == '__main__':
    # Collect the game data as a structured array
    todays_games = collect_nba_game_data()

    print("\nGames (AWAY vs HOME):")
    for game_info in todays_games:
        print(f"Game {game_info[0]}: {game_info[1]} vs {game_info[2]}")