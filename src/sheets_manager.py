"""
Google Sheets Manager
Handles all interactions with Google Sheets API
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
import os


class SheetsManager:
    """Manages Google Sheets operations for property comparison data"""
    
    def __init__(self, 
                 credentials_file: str = 'credentials.json',
                 spreadsheet_name: str = 'Property_Comparison_Data'):
        """
        Initialize Google Sheets connection
        
        Args:
            credentials_file: Path to credentials JSON file
            spreadsheet_name: Name of the Google Sheet
        """
        self.credentials_file = credentials_file
        self.spreadsheet_name = spreadsheet_name
        self.client = None
        self.workbook = None
        self._connected = False
        
        # Check if credentials file exists
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(
                f"Credentials file '{credentials_file}' not found. "
                "Please create a Google Service Account and download credentials.json"
            )
        
        try:
            # Define scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Authenticate using modern google-auth
            creds = Credentials.from_service_account_file(
                credentials_file, scopes=scope
            )
            self.client = gspread.authorize(creds)
            
            # Open workbook
            try:
                self.workbook = self.client.open(spreadsheet_name)
                self._connected = True
                print(f"✅ Connected to Google Sheet: {spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                raise ValueError(
                    f"Spreadsheet '{spreadsheet_name}' not found. "
                    "Make sure you've shared it with the service account email."
                )
            except Exception as e:
                raise ConnectionError(
                    f"Failed to connect to Google Sheets: {str(e)}. "
                    "Check your internet connection and credentials."
                )
        except FileNotFoundError:
            raise
        except Exception as e:
            raise ConnectionError(
                f"Failed to authenticate with Google Sheets: {str(e)}. "
                "Please check your credentials.json file and network connection."
            )
    
    def read_sheet(self, 
                   sheet_name: str,
                   as_dataframe: bool = True) -> pd.DataFrame | List[Dict]:
        """
        Read data from a sheet
        
        Args:
            sheet_name: Name of the sheet tab
            as_dataframe: Return as pandas DataFrame (default) or list of dicts
        
        Returns:
            DataFrame or list of dictionaries
        """
        if not self._connected:
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            worksheet = self.workbook.worksheet(sheet_name)
            data = worksheet.get_all_records()
            
            if as_dataframe:
                if not data:
                    # Return empty DataFrame with proper structure
                    return pd.DataFrame()
                return pd.DataFrame(data)
            return data
        except gspread.WorksheetNotFound:
            raise ValueError(f"Sheet '{sheet_name}' not found in workbook")
        except Exception as e:
            raise ConnectionError(f"Error reading sheet '{sheet_name}': {str(e)}")
    
    def write_dataframe(self, sheet_name: str, df: pd.DataFrame, clear_first: bool = True):
        """
        Write DataFrame to sheet
        
        Args:
            sheet_name: Name of the sheet tab
            df: pandas DataFrame to write
            clear_first: Clear existing content first (default True)
        """
        worksheet = self.workbook.worksheet(sheet_name)
        
        if clear_first:
            worksheet.clear()
        
        # Convert DataFrame to list of lists (including header)
        data = [df.columns.values.tolist()] + df.values.tolist()
        
        # Update sheet
        worksheet.update('A1', data)
        print(f"✅ Written {len(df)} rows to sheet '{sheet_name}'")
    
    def append_row(self, sheet_name: str, row_data: List[Any]):
        """
        Append a single row to sheet
        
        Args:
            sheet_name: Name of the sheet tab
            row_data: List of values to append
        """
        worksheet = self.workbook.worksheet(sheet_name)
        worksheet.append_row(row_data)
    
    def append_rows(self, sheet_name: str, rows_data: List[List[Any]]):
        """
        Append multiple rows to sheet
        
        Args:
            sheet_name: Name of the sheet tab
            rows_data: List of lists to append
        """
        worksheet = self.workbook.worksheet(sheet_name)
        for row in rows_data:
            worksheet.append_row(row)
        print(f"✅ Appended {len(rows_data)} rows to sheet '{sheet_name}'")
    
    def update_cell(self, 
                    sheet_name: str, 
                    row: int, 
                    col: int, 
                    value: Any):
        """
        Update a specific cell
        
        Args:
            sheet_name: Name of the sheet tab
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: Value to set
        """
        worksheet = self.workbook.worksheet(sheet_name)
        worksheet.update_cell(row, col, value)
    
    def find_and_update(self, 
                       sheet_name: str,
                       search_col: str,
                       search_value: str,
                       update_col: str,
                       update_value: Any):
        """
        Find a row by value and update a specific column
        
        Args:
            sheet_name: Name of the sheet tab
            search_col: Column name to search in
            search_value: Value to search for
            update_col: Column name to update
            update_value: New value
        """
        worksheet = self.workbook.worksheet(sheet_name)
        
        # Get header row
        headers = worksheet.row_values(1)
        
        try:
            search_col_idx = headers.index(search_col) + 1
            update_col_idx = headers.index(update_col) + 1
        except ValueError as e:
            raise ValueError(f"Column not found: {e}")
        
        # Find the cell
        cell = worksheet.find(search_value)
        
        if cell:
            # Update the corresponding cell in the update column
            worksheet.update_cell(cell.row, update_col_idx, update_value)
            print(f"✅ Updated {search_col}={search_value}, set {update_col}={update_value}")
        else:
            print(f"⚠️ Value '{search_value}' not found in column '{search_col}'")
    
    def get_sheet_names(self) -> List[str]:
        """Get list of all sheet names in workbook"""
        return [ws.title for ws in self.workbook.worksheets()]
    
    def create_sheet(self, sheet_name: str, rows: int = 1000, cols: int = 26):
        """
        Create a new sheet
        
        Args:
            sheet_name: Name for the new sheet
            rows: Number of rows (default 1000)
            cols: Number of columns (default 26)
        """
        try:
            worksheet = self.workbook.add_worksheet(title=sheet_name, rows=rows, cols=cols)
            print(f"✅ Created sheet '{sheet_name}'")
            return worksheet
        except gspread.exceptions.APIError as e:
            print(f"⚠️ Sheet '{sheet_name}' might already exist: {e}")
    
    def setup_headers(self, sheet_name: str, headers: List[str]):
        """
        Set up column headers in a sheet
        
        Args:
            sheet_name: Name of the sheet tab
            headers: List of column header names
        """
        worksheet = self.workbook.worksheet(sheet_name)
        worksheet.update('A1', [headers])
        print(f"✅ Set up {len(headers)} headers in sheet '{sheet_name}'")


# Test connection function
def test_connection():
    """Test Google Sheets connection"""
    try:
        sheets = SheetsManager()
        print("\n📊 Available sheets:")
        for name in sheets.get_sheet_names():
            print(f"  - {name}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when executed directly
    test_connection()




