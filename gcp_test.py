import datetime
import gspread
import os
import json
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from nba_scraper import collect_nba_game_data, update_game_results

# Constants
START_CELL = "A3"
NUM_COLUMNS = 6

# OAuth2 scope
scopes = ['https://www.googleapis.com/auth/spreadsheets']

load_dotenv()
json_credentials = os.getenv('JSON_CREDENTIALS')

json_credentials = json_credentials.strip("'")
credentials_dict = json.loads(json_credentials)
credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
client = gspread.authorize(credentials)

# List of Google Sheets with unique IDs and worksheet GIDs
sheets_info = [
    {"sheet_id": os.getenv('SHEET_ID_1'), "worksheet_GID": os.getenv('WORKSHEET_GID_1'), "name": "Personal"},
    {"sheet_id": os.getenv('SHEET_ID_2'), "worksheet_GID": os.getenv('WORKSHEET_GID_2'), "name": "Shared"},
]

def create_outer_border(sheet_id, worksheet_gid, start_cell, num_rows, num_columns):
    service = build('sheets', 'v4', credentials=credentials)

    start_column = ord(start_cell[0].upper()) - ord('A')
    start_row = int(start_cell[1:]) - 1  # subtract 1 to match 0-based index

    requests = [{
        'updateBorders': {
            'range': {
                'sheetId': int(worksheet_gid),  
                'startRowIndex': start_row,  
                'endRowIndex': start_row + num_rows,
                'startColumnIndex': start_column,
                'endColumnIndex': start_column + num_columns
            },
            'top': {'style': 'SOLID', 'width': 1, 'color': {'red': 0, 'green': 0, 'blue': 0}},
            'bottom': {'style': 'SOLID', 'width': 1, 'color': {'red': 0, 'green': 0, 'blue': 0}},
            'left': {'style': 'SOLID', 'width': 1, 'color': {'red': 0, 'green': 0, 'blue': 0}},
            'right': {'style': 'SOLID', 'width': 1, 'color': {'red': 0, 'green': 0, 'blue': 0}}
        }
    }]

    body = {'requests': requests}
    service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

    print(f"Outer border created on sheet {worksheet_gid} from {start_cell} spanning {num_rows} rows and {num_columns} columns.")

def insert_cells_and_shift_down(sheet_id, worksheet_gid, start_cell, num_rows, num_columns):
    service = build('sheets', 'v4', credentials=credentials)

    start_column = ord(start_cell[0].upper()) - ord('A')
    start_row = int(start_cell[1:]) - 1

    # create request to insert cells and shift down
    requests = [{
        'insertRange': {
            'range': {
                'sheetId': int(worksheet_gid),
                'startRowIndex': start_row,
                'endRowIndex': start_row + num_rows,
                'startColumnIndex': start_column,
                'endColumnIndex': start_column + num_columns
            },
            'shiftDimension': 'ROWS'
        }
    }]

    body = {'requests': requests}
    service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

    print(f"Inserted cells and shifted down on sheet {worksheet_gid} from {start_cell} spanning {num_rows} rows and {num_columns} columns.")

def update_game_results_in_sheets(sheets_info, game_results):
    for sheet_info in sheets_info:
        sheet_id = sheet_info["sheet_id"]
        worksheet_gid = sheet_info["worksheet_GID"]
        sheet_name = sheet_info["name"]
        
        print(f"Updating game results in {sheet_name}...")
        
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet_by_id(int(worksheet_gid))
        
        if worksheet is None:
            print(f"Error: Worksheet {worksheet_gid} not found in {sheet_name}!")
            continue

        # Create a list to store the batch update requests
        update_requests = []
        
        for i, game_info in game_results.items():
            row_number = i + 2  # A3
            winner = game_info['winner']

            if winner == "AWAY":
                away_team = worksheet.cell(row_number, 2).value
                update_requests.append({
                    'range': f'D{row_number}',
                    'values': [[away_team]]
                })
                print(f"Queued away team '{away_team}' to D{row_number} as the winner.")
            elif winner == "HOME":
                home_team = worksheet.cell(row_number, 3).value
                update_requests.append({
                    'range': f'D{row_number}',
                    'values': [[home_team]]
                })
                print(f"Queued home team '{home_team}' to D{row_number} as the winner.")
            else:
                print(f"Invalid winner value for game {i+1}: {winner}")

        # Perform the batch update
        if update_requests:
            worksheet.batch_update(update_requests)
            print(f"Game results updated in {sheet_name}.")

def update_todays_games_in_sheets(sheets_info, todays_games):
    if not todays_games:
        print("No games scheduled for today. Skipping update.")
        return
    
    num_rows = todays_games[-1][0]  # Get number of rows from last game index
    
    for sheet_info in sheets_info:
        sheet_id = sheet_info["sheet_id"]
        worksheet_gid = sheet_info["worksheet_GID"]
        sheet_name = sheet_info["name"]
        
        print(f"Updating today's games in {sheet_name}...")
        
        # Open the specific Google Sheet and Worksheet
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet_by_id(int(worksheet_gid))
        
        if worksheet is None:
            print(f"Error: Worksheet {worksheet_gid} not found in {sheet_name}!")
            continue

        insert_cells_and_shift_down(sheet_id, worksheet_gid, START_CELL, num_rows, NUM_COLUMNS)
        create_outer_border(sheet_id, worksheet_gid, START_CELL, num_rows, NUM_COLUMNS)
        
        # Add today's date to top left cell
        today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        worksheet.update_acell(START_CELL, today_date)

        # Store a list and append as a batch
        update_requests = []
        # Update cells from B:away to C:home columns
        for game_info in todays_games:
            row_number = game_info[0] + 2
            update_requests.append({
                'range': f'B{row_number}',
                'values': [[game_info[1].lower()]]
            })
            update_requests.append({
                'range': f'C{row_number}',
                'values': [[game_info[2].lower()]]
            })
        
        # Perform the batch update
        if update_requests:
            worksheet.batch_update(update_requests)
            print(f"Today's games updated in {sheet_name}.")

def main():
    try:
        print("Collecting NBA game data...")
        todays_games = collect_nba_game_data()
        
        print("Collecting game results from yesterday...")
        game_results = update_game_results()
        
        if game_results:
            update_game_results_in_sheets(sheets_info, game_results)
            print("Yesterday's game results updated!")
        else:
            print("No game results to update from yesterday.")
        
        if todays_games:
            update_todays_games_in_sheets(sheets_info, todays_games)
            print("Today's games updated!")
        else:
            print("No games scheduled for today.")
            
        print("Update complete for all sheets!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
