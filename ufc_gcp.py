import datetime
import gspread
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from ufc_scraper import collect_ufc_fight_data

# OAuth2 scope
scopes = ['https://www.googleapis.com/auth/spreadsheets']

# Load environment variables
load_dotenv('.env.ufc')
sheet_id = os.getenv('SHEET_ID')
worksheet_gid = os.getenv('WORKSHEET_GID')
json_credentials = os.getenv('JSON_CREDENTIALS')

# Load service account from JSON credentials
credentials = Credentials.from_service_account_file(json_credentials, scopes=scopes)
client = gspread.authorize(credentials)

# Open the spreadsheet by its specified ID
sheet = client.open_by_key(sheet_id)

worksheet = sheet.get_worksheet_by_id(int(worksheet_gid))
if worksheet is None:
    raise ValueError(f"No worksheet found with GID: {worksheet_gid}")

def create_outer_border(sheet_id, worksheet_gid, start_cell, num_rows, num_columns):
    """
    Creates an outer border around the specified range in Google Sheets.
    """
    service = build('sheets', 'v4', credentials=credentials)

    start_column = ord(start_cell[0].upper()) - ord('A')
    start_row = int(start_cell[1:]) - 1

    requests = [{
        'updateBorders': {
            'range': {
                'sheetId': worksheet_gid,
                'startRowIndex': start_row,
                'endRowIndex': start_row + num_rows,
                'startColumnIndex': start_column,
                'endColumnIndex': start_column + num_columns
            },
            'top': {'style': 'SOLID', 'width': 1, 'color': {'red': 0, 'green': 0, 'blue': 0}},
            'bottom': {'style': 'SOLID', 'width': 1, 'color': {'red': 0, 'green': 0, 'blue': 0}},
            'left': {'style': 'SOLID', 'width': 1, 'color': {'red': 0, 'green': 0, 'blue': 0}},
            'right': {'style': 'SOLID', 'width': 1, 'color': {'red': 0, 'green': 0, 'blue': 0}},
        }
    }]

    body = {'requests': requests}
    service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

    print(f"Outer border created from {start_cell} spanning {num_rows} rows and {num_columns} columns.")


def insert_cells_and_shift_down(sheet_id, worksheet_gid, start_cell, num_rows, num_columns):
    """
    Inserts empty cells and shifts the range down in Google Sheets.
    """
    service = build('sheets', 'v4', credentials=credentials)

    start_column = ord(start_cell[0].upper()) - ord('A')
    start_row = int(start_cell[1:]) - 1

    requests = [{
        'insertRange': {
            'range': {
                'sheetId': worksheet_gid,
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

    print(f"Inserted cells and shifted down from {start_cell} spanning {num_rows} rows and {num_columns} columns.")


def update_todays_ufc_fights_in_sheet(worksheet, start_cell, fights_data):
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')
    worksheet.update_acell(start_cell, today_date)

    # Update cells with UFC fight data
    for fight in fights_data:
        row_number = fight["fight_index"] + 2
        worksheet.update(values=[[fight["fighter_1"]]], range_name=f'B{row_number}')
        worksheet.update(values=[[fight["fighter_2"]]], range_name=f'C{row_number}')

if __name__ == "__main__":
    todays_fights = collect_ufc_fight_data()

    # Define the start range dimensions
    start_cell = "A3"
    num_rows = len(todays_fights)
    num_columns = 6

    # Update the Google Sheet
    insert_cells_and_shift_down(sheet_id, worksheet_gid, start_cell, num_rows, num_columns)
    create_outer_border(sheet_id, worksheet_gid, start_cell, num_rows, num_columns)
    update_todays_ufc_fights_in_sheet(worksheet, start_cell, todays_fights)

    print("Updated UFC fights in the Google Sheet!")