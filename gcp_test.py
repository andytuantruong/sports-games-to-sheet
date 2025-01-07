import gspread
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from nba_scraper import collect_nba_game_data

# oauth2 scope
scopes = ['https://www.googleapis.com/auth/spreadsheets']

load_dotenv()
sheet_id = os.getenv('SHEET_ID')
worksheet_gid = os.getenv('WORKSHEET_GID')
json_credentials = os.getenv('JSON_CREDENTIALS')

# load service account from json credentials
credentials = Credentials.from_service_account_file(json_credentials, scopes=scopes)

client = gspread.authorize(credentials)

# open the spreadsheet by its title
sheet = client.open_by_key(sheet_id)

# A3 will always be the starting point for the date
worksheet = sheet.sheet1

# worksheet.update_acell('A3', '9/10/2024')
# print("Cell A3 updated with today's date")

# creating an outer border around games of the day
def create_outer_border(sheet_id, worksheet_gid, start_cell, num_rows, num_columns):
    # using Google Sheets API service
    service = build('sheets', 'v4', credentials=credentials)

    start_column = ord(start_cell[0].upper()) - ord('A')  # convert 'A' to 0, 'B' to 1, etc.
    start_row = int(start_cell[1:]) - 1  # subtract 1 to match 0-based index

    # create border around day games 
    requests = [{
        'updateBorders': {
            'range': {
                'sheetId': worksheet_gid,  
                'startRowIndex': start_row,  
                'endRowIndex': start_row + num_rows,  # add num_rows to starting row
                'startColumnIndex': start_column,
                'endColumnIndex': start_column + num_columns  # add num_columns to starting column
            },
            'top': {
                'style': 'SOLID',
                'width': 1,
                'color': {'red': 0, 'green': 0, 'blue': 0}
            },
            'bottom': {
                'style': 'SOLID',
                'width': 1,
                'color': {'red': 0, 'green': 0, 'blue': 0}
            },
            'left': {
                'style': 'SOLID',
                'width': 1,
                'color': {'red': 0, 'green': 0, 'blue': 0}
            },
            'right': {
                'style': 'SOLID',
                'width': 1,
                'color': {'red': 0, 'green': 0, 'blue': 0}
            }
        }
    }]

    body = {
        'requests': requests
    }

    response = service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

    print(f"Outer border created from {start_cell} spanning {num_rows} rows and {num_columns} columns.")

def insert_cells_and_shift_down(sheet_id, worksheet_gid, start_cell, num_rows, num_columns):
    # using Google Sheets API service
    service = build('sheets', 'v4', credentials=credentials)

    start_column = ord(start_cell[0].upper()) - ord('A')  
    start_row = int(start_cell[1:]) - 1  

    # create request to insert cells and shift down
    requests = [{
        'insertRange': {
            'range': {
                'sheetId': worksheet_gid,  
                'startRowIndex': start_row,
                'endRowIndex': start_row + num_rows,
                'startColumnIndex': start_column,
                'endColumnIndex': start_column + num_columns
            },
            'shiftDimension': 'ROWS'  # shift down
        }
    }]

    body = {
        'requests': requests
    }

    response = service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

    print(f"Inserted cells and shifted down from {start_cell} spanning {num_rows} rows and {num_columns} columns.")

if __name__ == "__main__":
    todays_games = collect_nba_game_data()
    
    start_cell = "A3"
    
    # set to last index
    num_rows = todays_games[-1][0]
    num_columns = 6

    insert_cells_and_shift_down(sheet_id, worksheet_gid, start_cell, num_rows, num_columns)
    create_outer_border(sheet_id, worksheet_gid, start_cell, num_rows, num_columns)

    # update cells from B to C column with away to home teams
    for game_info in todays_games:
        row_number = game_info[0] + 2
        worksheet.update(f'B{row_number}', [[game_info[1]]])
        worksheet.update(f'C{row_number}', [[game_info[2]]])