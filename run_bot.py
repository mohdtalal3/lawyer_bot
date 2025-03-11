import time
import sys
import gspread
from google.oauth2.service_account import Credentials
import specialty_extractor
import re
from time import sleep
import random

class LeadProcessor:
    def __init__(self, sheet_id, sheet_name, delay=60):
        self.credentials_file = 'credentials.json'
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.delay = float(delay)
        self.should_stop = False
        self.base_delay = 80
        self.max_retries = 5
        self.processed_sheet_name = "processed_lawyers"
        self.connection_retry_delay = 300
        self.max_connection_retries = 3
        self.processed_urls = set()  # Keep track of processed URLs

    def setup_google_sheets(self):
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        try:
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(self.sheet_id)
            
            # Get the main sheet
            try:
                leads_sheet = spreadsheet.worksheet(self.sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                print(f"Sheet '{self.sheet_name}' not found!")
                return None, None

            # Check if processed_lawyers sheet exists, if not create it
            try:
                processed_sheet = spreadsheet.worksheet(self.processed_sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                print(f"Creating new sheet '{self.processed_sheet_name}'...")
                processed_sheet = spreadsheet.add_worksheet(
                    title=self.processed_sheet_name,
                    rows=1000,
                    cols=20
                )
                # Copy headers from main sheet
                headers = leads_sheet.row_values(1)
                processed_sheet.update('A1', [headers])
                
            return leads_sheet, processed_sheet
            
        except Exception as e:
            print(f"Error setting up Google Sheets: {str(e)}")
            return None, None

    def update_sheet_with_backoff(self, leads_sheet, update_cells):
        """
        Update sheet with exponential backoff retry mechanism
        """
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                leads_sheet.update_cells(update_cells)
                return True
            except Exception as e:
                if "Quota exceeded" in str(e) or "429" in str(e):
                    retry_count += 1
                    if retry_count == self.max_retries:
                        raise Exception(f"Max retries ({self.max_retries}) exceeded for API quota limit")
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(300, self.base_delay * (2 ** retry_count) + random.uniform(0, 10))
                    print(f"\n⚠️ Rate limit hit! Waiting {delay:.1f} seconds before retry {retry_count}/{self.max_retries}")
                    sleep(delay)
                else:
                    raise e
        return False

    def move_to_processed(self, leads_sheet, processed_sheet, row_idx, row_data):
        """Move a row to the processed sheet with exponential backoff"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                # Get the next empty row in processed sheet
                processed_values = processed_sheet.get_all_values()
                next_row = len(processed_values) + 1

                # Add row to processed sheet
                processed_sheet.insert_row(row_data, next_row)
                print(f"Successfully moved row {row_idx+1} to processed sheet")
                return True
                
            except Exception as e:
                if "Quota exceeded" in str(e) or "429" in str(e):
                    retry_count += 1
                    if retry_count == self.max_retries:
                        print(f"Max retries ({self.max_retries}) exceeded for moving row to processed sheet")
                        return False
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(300, self.base_delay * (2 ** retry_count) + random.uniform(0, 10))
                    print(f"\n⚠️ Rate limit hit while moving to processed sheet! Waiting {delay:.1f} seconds before retry {retry_count}/{self.max_retries}")
                    sleep(delay)
                else:
                    print(f"Error moving row to processed sheet: {str(e)}")
                    return False
        
        return False

    def process_single_lead(self, leads_sheet, processed_sheet, row_idx, row, headers):
        """Process a single lead"""
        try:
            # Extract indices and basic data
            first_name_index = headers.index("First Name")
            last_name_index = headers.index("Last Name")
            city_index = headers.index("CITY")
            url_index = headers.index("doctrineURL")
            specialty_indices = []
            for i in range(1, 6):
                specialty_indices.append(headers.index(f"speciality {i}"))
            serment_index = headers.index("Serment")
            
            # Extract data
            first_name = row[first_name_index].strip()
            last_name = row[last_name_index].strip()
            city = row[city_index].strip()
            current_url = row[url_index].strip() if url_index < len(row) else ""

            # Check if URL is already processed
            if current_url and "doctrine.fr/p/avocat" in current_url:
                if current_url in self.processed_urls:
                    print(f"Skipping already processed: {first_name} {last_name} ({current_url})")
                    return
                print(f"Starting new: {first_name} {last_name} ({current_url})")

            if not first_name or not last_name or not city:
                print(f"Missing required data for row {row_idx+1}")
                return

            print(f"Processing: {first_name} {last_name} in {city}")
            
            # Extract specialties and oath date
            specialties, oath_date, lawyer_url = specialty_extractor.extract_lawyer_data(
                first_name, last_name, city
            )

            # Initialize update cells
            update_cells = []
            
            # Update specialties (up to 5)
            for i, idx in enumerate(specialty_indices):
                specialty_value = "None"
                if specialties and i < len(specialties):
                    specialty_value = specialties[i]
                update_cells.append(gspread.Cell(row_idx+1, idx+1, specialty_value))
            
            # Update oath date and URL
            update_cells.append(gspread.Cell(row_idx+1, serment_index+1, oath_date))
            update_cells.append(gspread.Cell(row_idx+1, url_index+1, lawyer_url))
            
            # Update the sheet
            if update_cells:
                self.update_sheet_with_backoff(leads_sheet, update_cells)
                updated_row = leads_sheet.row_values(row_idx + 1)
                
                # Check if we have both valid URL and oath date
                url_value = updated_row[url_index].strip()
                oath_date_value = updated_row[serment_index].strip()
                
                has_valid_url = url_value and url_value not in ["None", "Not found"]
                has_valid_oath = oath_date_value and oath_date_value != "Not found"
                
                if has_valid_url and has_valid_oath:
                    # Move to processed sheet and delete
                    if self.move_to_processed(leads_sheet, processed_sheet, row_idx, updated_row):
                        try:
                            leads_sheet.delete_rows(row_idx + 1)
                            print(f"Successfully moved and deleted row {row_idx+1}")
                        except Exception as e:
                            print(f"Error deleting row {row_idx+1}: {str(e)}")
                else:
                    missing_items = []
                    if not has_valid_url:
                        missing_items.append("URL")
                    if not has_valid_oath:
                        missing_items.append("oath date")
                    print(f"Row {row_idx+1} kept for retry: Missing {' and '.join(missing_items)}")
            
            print(f"Successfully processed {first_name} {last_name}")
            
            # Add URL to processed set if successful
            if lawyer_url:
                self.processed_urls.add(lawyer_url)
                print(f"Added to processed: {lawyer_url}")

        except Exception as e:
            print(f"Error processing row {row_idx+1}: {str(e)}")

    def process_leads(self):
        leads_sheet, processed_sheet = self.setup_google_sheets()
        if not leads_sheet or not processed_sheet:
            return

        while not self.should_stop:
            try:
                # Get all records
                all_values = leads_sheet.get_all_values()
                if len(all_values) <= 1:
                    print("No new leads to process. Waiting...")
                    time.sleep(self.delay)
                    continue

                headers = [h.strip() for h in all_values[0]]
                url_index = headers.index("doctrineURL")
                
                # Process rows from bottom to top
                for row_idx in range(len(all_values) - 1, 0, -1):
                    row = all_values[row_idx]
                    current_url = row[url_index].strip() if url_index < len(row) else ""
                    
                    # Skip if URL is already processed
                    if current_url and "doctrine.fr/p/avocat" in current_url:
                        if current_url in self.processed_urls:
                            continue
                    
                    self.process_single_lead(leads_sheet, processed_sheet, row_idx, row, headers)
                    time.sleep(random.uniform(1, 2))  # Small delay between processing
                
                print(f"\nWaiting {self.delay} seconds before checking for new leads...")
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"Main process error: {str(e)}")
                time.sleep(self.delay)
                continue

def main():
    print("Starting Lawyer Data Extractor...")
    print("Using credentials from: credentials.json")
    
    # Get Sheet ID from user
    sheet_id = input("Enter Google Sheet ID (required): ").strip()
    while not sheet_id:
        sheet_id = input("Sheet ID is required. Please enter Google Sheet ID: ").strip()
    
    # Get Sheet Name from user (default: leads)
    sheet_name = input("Enter Sheet Name (press Enter for default 'FRANCE: 78000 lawyers'): ").strip()
    if not sheet_name:
        sheet_name = "FRANCE: 78000 lawyers"
    
    # Get delay from user (default: 60)
    while True:
        delay_input = input("Enter check interval in seconds (press Enter for default 5): ").strip()
        if not delay_input:
            delay = 5
            break
        try:
            delay = float(delay_input)
            if delay <= 0:
                print("Delay must be a positive number!")
                continue
            break
        except ValueError:
            print("Please enter a valid number!")
    
    print("\nStarting with following settings:")
    print(f"Sheet ID: {sheet_id}")
    print(f"Sheet Name: {sheet_name}")
    print(f"Check Interval: {delay} seconds")
    print("\nPress Ctrl+C to stop the process\n")
    
    try:
        processor = LeadProcessor(sheet_id=sheet_id, sheet_name=sheet_name, delay=delay)
        processor.process_leads()
    except KeyboardInterrupt:
        print("\nStopping the process...")
        sys.exit(0)

if __name__ == "__main__":
    main()