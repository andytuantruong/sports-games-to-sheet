import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# oauth2 scope
scopes = ['https://www.googleapis.com/auth/spreadsheets']

# load service account from json credentials
credentials = Credentials.from_service_account_file('mlb-games-to-sheet-5c493b26bc92.json', scopes=scopes)

sheet_id = "1uOkUgiZFvxMly0IRdnKMFVesa75M8FTtlnInhUPc3fk"

client = gspread.authorize(credentials)

# open the spreadsheet by its title
sheet  = client.open_by_key(sheet_id)

# A3 will always be the starting point for the date
worksheet = sheet.sheet1
worksheet.update_acell('A3', '9/10/2024')
print("Cell A3 updated with today's date")

# creating an outer border around games of the day
def create_outer_border(sheet_id, start_cell, num_rows, num_columns):
    # using Google Sheets API service
    service = build('sheets', 'v4', credentials=credentials)
    
    # parse the start_cell 
    start_column = ord(start_cell[0].upper()) - ord('A')  # convert 'A' to 0, 'B' to 1, etc.
    start_row = int(start_cell[1:]) - 1  # subtract 1 to match 0-based index

    # define the outer border style
    requests = [{
        'updateBorders': {
            'range': {
                'sheetId': 0,  # first sheet
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


if __name__ == "__main__":
    start_cell = "A3"
    num_rows = 9 # to be changed based on number of games played
    num_columns = 6  # always A to F 

    create_outer_border(sheet_id, start_cell, num_rows, num_columns)