import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

load_dotenv(".ufc.env")

def collect_ufc_fight_data():
    driver = webdriver.Firefox()
    try:
        ufc_url = os.getenv("UFC_URL")
        if not ufc_url:
            raise ValueError("UFC_URL not found in the environment variables.")

        driver.get(ufc_url)
        time.sleep(2)

        # Locate the list of fights
        fight_list = driver.find_elements(By.CSS_SELECTOR, "ul.mt-5[data-event-view-toggle-target='list'] li.border-b.border-dotted.border-tap_6")
        print(f"Found {len(fight_list)} fights.")

        fights_data = []

        for index, fight in enumerate(fight_list, start=1):
            try:
                # Extract fighter names
                fighter1 = fight.find_element(By.CSS_SELECTOR, "div.hidden.md\\:flex.order-1.text-sm.text-tap_3 .link-primary-red").text
                fighter2 = fight.find_element(By.CSS_SELECTOR, "div.hidden.md\\:flex.order-2.text-sm.text-tap_3 .link-primary-red").text

                # Append to results
                fights_data.append({
                    "fight_index": index,
                    "fighter_1": fighter1,
                    "fighter_2": fighter2,
                })
                print(f"Fight {index}: {fighter1} vs {fighter2}")

            except NoSuchElementException as e:
                print(f"Error extracting data for fight {index}: {e}")
                fights_data.append({
                    "fight_index": index,
                    "fighter_1": "N/A",
                    "fighter_2": "N/A",
                })

        return fights_data

    finally:
        driver.quit()

if __name__ == "__main__":
    ufc_fights = collect_ufc_fight_data()

    print("\nCollected UFC Fights:")
    for fight in ufc_fights:
        print(f"Fight {fight['fight_index']}: {fight['fighter_1']} vs {fight['fighter_2']}")
