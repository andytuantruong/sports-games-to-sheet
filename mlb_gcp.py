import datetime
import gspread
import os
import time
import random
from functools import wraps
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from mlb_scraper import collect_mlb_game_data, update_game_results

# Constants
START_CELL = "A3"
NUM_COLUMNS = 6

def retry_with_backoff(max_retries=5, initial_delay=5):
    """
    Decorator that implements retry logic with exponential backoff for API calls.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        initial_delay (int): Initial delay in seconds before first retry
        
    Returns:
        function: Decorated function with retry logic
    """
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

# Load MLB-specific environment variables
load_dotenv('.mlb.env')
json_credentials = os.getenv('JSON_CREDENTIALS')

# load service account from JSON credentials file
credentials = Credentials.from_service_account_file(json_credentials, scopes=scopes)
client = gspread.authorize(credentials)

# List of Google Sheets with unique IDs and worksheet GIDs for MLB
sheets_info = [
    {"sheet_id": os.getenv('SHEET_ID'), "worksheet_GID": os.getenv('WORKSHEET_GID'), "name": "MLB Sheet"},
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
    """
    Create an outer border around a range of cells in a Google Sheet.
    
    Args:
        sheet_id (str): Google Sheet ID
        worksheet_gid (str): Worksheet GID
        start_cell (str): Starting cell (e.g., "A3")
        num_rows (int): Number of rows to include in the border
        num_columns (int): Number of columns to include in the border
    """
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
    """
    Insert cells and shift existing cells down in a Google Sheet.
    
    Args:
        sheet_id (str): Google Sheet ID
        worksheet_gid (str): Worksheet GID
        start_cell (str): Starting cell (e.g., "A3")
        num_rows (int): Number of rows to insert
        num_columns (int): Number of columns to span
    """
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


def update_tomorrows_games_in_sheets(sheets_info, tomorrows_games):
    """
    Update tomorrow's MLB games in Google Sheets.
    
    Args:
        sheets_info (list): List of sheet information dictionaries
        tomorrows_games (list): List of tomorrow's games
    """
    if not tomorrows_games:
        print("No MLB games scheduled for tomorrow. Skipping update.")
        return
    
    num_rows = tomorrows_games[-1][0]  # Get number of rows from last game index
    
    for sheet_info in sheets_info:
        sheet_id = sheet_info["sheet_id"]
        worksheet_gid = sheet_info["worksheet_GID"]
        sheet_name = sheet_info["name"]
        
        print(f"Updating tomorrow's MLB games in {sheet_name}...")
        
        # Open the specific Google Sheet and Worksheet
        sheet = open_sheet_by_key(client, sheet_id)
        worksheet = get_worksheet_by_id(sheet, worksheet_gid)
        
        if worksheet is None:
            print(f"Error: Worksheet {worksheet_gid} not found in {sheet_name}!")
            continue

        insert_cells_and_shift_down(sheet_id, worksheet_gid, START_CELL, num_rows, NUM_COLUMNS)
        create_outer_border(sheet_id, worksheet_gid, START_CELL, num_rows, NUM_COLUMNS)
        
        # Add tomorrow's date to top left cell
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        tomorrow_date = tomorrow.strftime('%Y-%m-%d')
        update_acell(worksheet, START_CELL, tomorrow_date)

        # Store a list and append as a batch
        update_requests = []
        # Update cells from B:away to C:home columns
        for game_info in tomorrows_games:
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
            print(f"Tomorrow's MLB games updated in {sheet_name}.")

def update_game_results_in_sheets(sheets_info, game_results):
    for sheet_info in sheets_info:
        sheet_id = sheet_info["sheet_id"]
        worksheet_gid = sheet_info["worksheet_GID"]
        sheet_name = sheet_info["name"]
        
        print(f"Updating MLB game results in {sheet_name}...")
        
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
            print(f"MLB game results updated in {sheet_name}.")

def main():
    try:
        print("Collecting MLB game data for tomorrow...")
        tomorrows_games = collect_mlb_game_data()
        
        print("Collecting MLB game results from yesterday...")
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        yesterday_date = yesterday.strftime('%Y-%m-%d')
        game_results = update_game_results(yesterday_date)
        
        if game_results:
            update_game_results_in_sheets(sheets_info, game_results)
            print("Yesterday's MLB game results updated!")
        else:
            print("No MLB game results to update from yesterday.")
        
        if tomorrows_games:
            update_tomorrows_games_in_sheets(sheets_info, tomorrows_games)
            print("Tomorrow's MLB games updated!")
        else:
            print("No MLB games scheduled for tomorrow.")
            
        print("MLB update complete for all sheets!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 