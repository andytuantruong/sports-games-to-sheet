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

    # List of game info
    for index, game_element in enumerate(game_elements, start=1):
        print("Game Element", index)
        print("Tag Name:", game_element.tag_name)
        print("Text Content:", game_element.text)
        print("Class:", game_element.get_attribute('class'))
        print("-" * 100)

    game_list = []
    game_index = 1
    for game_element in game_elements:
        lines = game_element.text.split('\n')
        
        away_team_abbrev = lines[3] if len(lines) > 3 else "N/A"
        home_team_abbrev = lines[4] if len(lines) > 4 else "N/A"

        # (away vs home)
        game_versus = {
            'game_index': game_index,
            'away_team_abbrev': away_team_abbrev,
            'home_team_abbrev': home_team_abbrev
        }

        game_list.append(game_versus)

        print("Game", game_index)
        print("Away Team Abbreviation:", away_team_abbrev)
        print("Home Team Abbreviation:", home_team_abbrev)
        print()

        game_index += 1

    driver.close()

    print(game_list)
    return game_list

if __name__ == '__main__':
    collect_nba_game_data()
