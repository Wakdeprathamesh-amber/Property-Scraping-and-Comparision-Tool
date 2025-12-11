"""
CSV Processor
Handles CSV upload, validation, and writing to Google Sheets
"""

import pandas as pd
from datetime import datetime
from typing import Tuple, List
from pathlib import Path
from src.sheets_manager import SheetsManager
from src.utils.logger import setup_logger


class CSVProcessor:
    """Process CSV files containing property URL pairs"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.sheets = SheetsManager()
    
    def validate_csv(self, csv_path: str) -> Tuple[bool, str, pd.DataFrame]:
        """
        Validate CSV format and content
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Tuple of (is_valid, error_message, dataframe)
        """
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Check if file is empty
            if len(df) == 0:
                return False, "CSV file is empty", None
            
            # Check required columns
            required_columns = ['Amber_URL', 'Uhomes_URL']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f"Missing required columns: {', '.join(missing_columns)}", None
            
            # Check for empty URLs
            empty_amber = df['Amber_URL'].isna().sum()
            empty_uhomes = df['Uhomes_URL'].isna().sum()
            
            if empty_amber > 0:
                return False, f"Found {empty_amber} empty Amber URLs", None
            if empty_uhomes > 0:
                return False, f"Found {empty_uhomes} empty Uhomes URLs", None
            
            # Validate URL format (basic check)
            def is_valid_url(url):
                url_str = str(url).strip()
                return url_str.startswith('http://') or url_str.startswith('https://')
            
            invalid_amber = df[~df['Amber_URL'].apply(is_valid_url)]
            invalid_uhomes = df[~df['Uhomes_URL'].apply(is_valid_url)]
            
            if len(invalid_amber) > 0:
                return False, f"Found {len(invalid_amber)} invalid Amber URLs (must start with http:// or https://)", None
            
            if len(invalid_uhomes) > 0:
                return False, f"Found {len(invalid_uhomes)} invalid Uhomes URLs (must start with http:// or https://)", None
            
            self.logger.info(f"✅ CSV validation passed: {len(df)} property pairs found")
            return True, "", df
            
        except FileNotFoundError:
            return False, f"File not found: {csv_path}", None
        except pd.errors.EmptyDataError:
            return False, "CSV file is empty", None
        except Exception as e:
            return False, f"Error reading CSV: {str(e)}", None
    
    def generate_property_ids(self, count: int, start_from: int = None) -> List[str]:
        """
        Generate Property IDs
        
        Args:
            count: Number of IDs to generate
            start_from: Starting number (if None, get from existing data)
            
        Returns:
            List of Property IDs
        """
        if start_from is None:
            # Get existing properties to determine next ID
            try:
                existing_df = self.sheets.read_sheet('Input_Properties')
                if len(existing_df) > 0:
                    # Extract numbers from existing IDs (format: P001, P002, etc.)
                    existing_ids = existing_df['Property_ID'].tolist()
                    numbers = []
                    for pid in existing_ids:
                        try:
                            num = int(pid.replace('P', ''))
                            numbers.append(num)
                        except:
                            continue
                    start_from = max(numbers) + 1 if numbers else 1
                else:
                    start_from = 1
            except:
                start_from = 1
        
        return [f'P{i:03d}' for i in range(start_from, start_from + count)]
    
    def process_csv(self, csv_path: str, append: bool = True) -> Tuple[bool, str, int]:
        """
        Process CSV and write to Google Sheets
        
        Args:
            csv_path: Path to CSV file
            append: If True, append to existing data. If False, replace all data.
            
        Returns:
            Tuple of (success, message, number_of_properties)
        """
        self.logger.info(f"Processing CSV file: {csv_path}")
        
        # Validate CSV
        is_valid, error_msg, df = self.validate_csv(csv_path)
        if not is_valid:
            self.logger.error(f"❌ Validation failed: {error_msg}")
            return False, error_msg, 0
        
        # Add Property IDs
        property_ids = self.generate_property_ids(len(df))
        df.insert(0, 'Property_ID', property_ids)
        
        # Add Status column
        df['Status'] = 'pending'
        
        # Add Created_At timestamp
        df['Created_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Reorder columns to match sheet structure
        df = df[['Property_ID', 'Amber_URL', 'Uhomes_URL', 'Status', 'Created_At']]
        
        try:
            if append:
                # Read existing data
                try:
                    existing_df = self.sheets.read_sheet('Input_Properties')
                    if len(existing_df) > 0:
                        # Append new data
                        combined_df = pd.concat([existing_df, df], ignore_index=True)
                        self.sheets.write_dataframe('Input_Properties', combined_df)
                        self.logger.info(f"✅ Appended {len(df)} properties (Total: {len(combined_df)})")
                    else:
                        # No existing data, just write
                        self.sheets.write_dataframe('Input_Properties', df)
                        self.logger.info(f"✅ Added {len(df)} properties")
                except:
                    # Sheet is empty or error reading, just write
                    self.sheets.write_dataframe('Input_Properties', df)
                    self.logger.info(f"✅ Added {len(df)} properties")
            else:
                # Replace all data
                self.sheets.write_dataframe('Input_Properties', df, clear_first=True)
                self.logger.info(f"✅ Replaced all data with {len(df)} properties")
            
            return True, f"Successfully processed {len(df)} property pairs", len(df)
            
        except Exception as e:
            error_msg = f"Error writing to Google Sheets: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return False, error_msg, 0
    
    def get_pending_properties(self) -> pd.DataFrame:
        """
        Get all properties with 'pending' status
        
        Returns:
            DataFrame of pending properties
        """
        try:
            df = self.sheets.read_sheet('Input_Properties')
            pending_df = df[df['Status'] == 'pending']
            self.logger.info(f"Found {len(pending_df)} pending properties")
            return pending_df
        except Exception as e:
            self.logger.error(f"Error fetching pending properties: {e}")
            return pd.DataFrame()
    
    def update_property_status(self, property_id: str, new_status: str):
        """
        Update status for a specific property
        
        Args:
            property_id: Property ID (e.g., 'P001')
            new_status: New status value
        """
        try:
            self.sheets.find_and_update(
                'Input_Properties',
                search_col='Property_ID',
                search_value=property_id,
                update_col='Status',
                update_value=new_status
            )
        except Exception as e:
            self.logger.error(f"Error updating status for {property_id}: {e}")


def main():
    """Test CSV processor with sample data"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.csv_processor <csv_file_path> [--replace]")
        print("\nExample:")
        print("  python -m src.csv_processor property_input_template.csv")
        print("  python -m src.csv_processor data.csv --replace")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    append_mode = '--replace' not in sys.argv
    
    processor = CSVProcessor()
    success, message, count = processor.process_csv(csv_path, append=append_mode)
    
    if success:
        print(f"\n✅ Success: {message}")
        print(f"\nYou can view the data in Google Sheets: Input_Properties tab")
        print(f"\nNext step: Run the scraping engine to process these {count} properties")
    else:
        print(f"\n❌ Error: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()




