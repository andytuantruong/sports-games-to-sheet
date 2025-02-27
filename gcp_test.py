import datetime
import gspread
import os
import time
import random
from functools import wraps
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from nba_scraper import collect_nba_game_data, update_game_results

# Constants
START_CELL = "A3"
NUM_COLUMNS = 6

def retry_with_backoff(max_retries=5, initial_delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if we've reached max retries
                    if attempt == max_retries - 1:
                        print(f"Failed after {max_retries} attempts: {str(e)}")
                        raise
                    
                    jitter = random.uniform(0, 1)
                    wait_time = delay + jitter
                    
                    print(f"Attempt {attempt + 1} failed with error: {str(e)}. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    
                    # Exponential backoff - double the delay for next attempt
                    delay *= 2
        return wrapper
    return decorator

# OAuth2 scope
scopes = ['https://www.googleapis.com/auth/spreadsheets']

load_dotenv()
json_credentials = os.getenv('JSON_CREDENTIALS')

# load service account from JSON credentials file
credentials = Credentials.from_service_account_file(json_credentials, scopes=scopes)
client = gspread.authorize(credentials)

# List of Google Sheets with unique IDs and worksheet GIDs
sheets_info = [
    {"sheet_id": os.getenv('SHEET_ID_1'), "worksheet_GID": os.getenv('WORKSHEET_GID_1'), "name": "Personal"},
    {"sheet_id": os.getenv('SHEET_ID_2'), "worksheet_GID": os.getenv('WORKSHEET_GID_2'), "name": "Shared"},
]

@retry_with_backoff()
def open_sheet_by_key(client, sheet_id):
    """Open a Google Sheet by its ID with retry logic."""
    return client.open_by_key(sheet_id)

@retry_with_backoff()
def get_worksheet_by_id(sheet, worksheet_id):
    """Get a worksheet by its ID with retry logic."""
    return sheet.get_worksheet_by_id(int(worksheet_id))

@retry_with_backoff()
def get_cell_value(worksheet, row, col):
    """Get a cell value with retry logic."""
    return worksheet.cell(row, col).value

@retry_with_backoff()
def batch_update(worksheet, update_requests):
    """Perform a batch update with retry logic."""
    worksheet.batch_update(update_requests)

@retry_with_backoff()
def update_acell(worksheet, cell, value):
    """Update a single cell with retry logic."""
    worksheet.update_acell(cell, value)

@retry_with_backoff()
def execute_batch_update(service, sheet_id, body):
    """Execute a batch update with retry logic."""
    return service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

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
    execute_batch_update(service, sheet_id, body)

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
    execute_batch_update(service, sheet_id, body)

    print(f"Inserted cells and shifted down on sheet {worksheet_gid} from {start_cell} spanning {num_rows} rows and {num_columns} columns.")

def update_game_results_in_sheets(sheets_info, game_results):
    for sheet_info in sheets_info:
        sheet_id = sheet_info["sheet_id"]
        worksheet_gid = sheet_info["worksheet_GID"]
        sheet_name = sheet_info["name"]
        
        print(f"Updating game results in {sheet_name}...")
        
        sheet = open_sheet_by_key(client, sheet_id)
        worksheet = get_worksheet_by_id(sheet, worksheet_gid)
        
        if worksheet is None:
            print(f"Error: Worksheet {worksheet_gid} not found in {sheet_name}!")
            continue

        # Create a list to store the batch update requests
        update_requests = []
        
        for i, game_info in game_results.items():
            row_number = i + 2  # A3
            winner = game_info['winner']

            if winner == "AWAY":
                away_team = get_cell_value(worksheet, row_number, 2)
                update_requests.append({
                    'range': f'D{row_number}',
                    'values': [[away_team]]
                })
                print(f"Queued away team '{away_team}' to D{row_number} as the winner.")
            elif winner == "HOME":
                home_team = get_cell_value(worksheet, row_number, 3)
                update_requests.append({
                    'range': f'D{row_number}',
                    'values': [[home_team]]
                })
                print(f"Queued home team '{home_team}' to D{row_number} as the winner.")
            else:
                print(f"Invalid winner value for game {i+1}: {winner}")

        # Perform the batch update
        if update_requests:
            batch_update(worksheet, update_requests)
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
        sheet = open_sheet_by_key(client, sheet_id)
        worksheet = get_worksheet_by_id(sheet, worksheet_gid)
        
        if worksheet is None:
            print(f"Error: Worksheet {worksheet_gid} not found in {sheet_name}!")
            continue

        insert_cells_and_shift_down(sheet_id, worksheet_gid, START_CELL, num_rows, NUM_COLUMNS)
        create_outer_border(sheet_id, worksheet_gid, START_CELL, num_rows, NUM_COLUMNS)
        
        # Add today's date to top left cell
        today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        update_acell(worksheet, START_CELL, today_date)

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
            batch_update(worksheet, update_requests)
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
