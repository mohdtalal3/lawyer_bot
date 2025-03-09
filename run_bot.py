import time
import sys
import gspread
from google.oauth2.service_account import Credentials
import link_extractor
import specialty_extractor
import re

class LeadProcessor:
    def __init__(self, sheet_id, sheet_name, delay=60):
        self.credentials_file = 'credentials.json'
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.delay = float(delay)
        self.should_stop = False
        
    def setup_google_sheets(self):
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        try:
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(self.sheet_id)
            
            # Get the specified sheet
            try:
                leads_sheet = spreadsheet.worksheet(self.sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                print(f"Sheet '{self.sheet_name}' not found!")
                return None
                
            return leads_sheet
            
        except Exception as e:
            print(f"Error setting up Google Sheets: {str(e)}")
            return None

    def process_leads(self):
        leads_sheet = self.setup_google_sheets()
        if not leads_sheet:
            return

        while not self.should_stop:
            try:
                # Get all records including empty rows
                all_values = leads_sheet.get_all_values()
                if not all_values:
                    print("Empty sheet. Waiting...")
                    time.sleep(self.delay)
                    continue
                    
                # Clean headers by removing trailing/leading spaces
                headers = [h.strip() for h in all_values[0]]
                
                if len(all_values) <= 1:  # Only headers or empty sheet
                    print("No new leads to process. Waiting...")
                    time.sleep(self.delay)
                    continue
                
                # Find required column indices
                try:
                    first_name_index = headers.index("First Name")
                    last_name_index = headers.index("Last Name")
                    city_index = headers.index("CITY")
                    specialty_indices = []
                    for i in range(1, 6):
                        specialty_indices.append(headers.index(f"speciality {i}"))
                    serment_index = headers.index("Serment")
                    url_index = headers.index("doctrineURL")
                except ValueError as e:
                    print(f"Required column not found in headers: {str(e)}")
                    return
                
                # Process each row starting from index 1 (after headers)
                for row_idx in range(1, len(all_values)):
                    if self.should_stop:
                        break
                        
                    row = all_values[row_idx]
                    
                    # Skip only if there's a valid doctrine.fr URL
                    if (row_idx < len(all_values) and 
                        url_index < len(row) and 
                        row[url_index].strip() and 
                        "doctrine.fr/p/avocat" in row[url_index].strip()):
                        continue
                    
                    # Convert row to dictionary using cleaned headers
                    data = {headers[i]: value for i, value in enumerate(row) if i < len(headers)}
                    
                    try:
                        # Extract first name, last name, and city
                        first_name = data.get("First Name", "").strip()
                        last_name = data.get("Last Name", "").strip()
                        city = data.get("CITY", "").strip()
                        
                        if not first_name or not last_name or not city:
                            print(f"Missing required data for row {row_idx+1}")
                            continue
                        
                        # Create search query
                        search_query = f"{first_name}+{last_name}+{city}+doctrine.fr"
                        search_url = f"https://www.bing.com/search?q={search_query}"
                        
                        print(f"Searching for: {first_name} {last_name} in {city}")
                        
                        # Extract link using link_extractor
                        doctrine_url = link_extractor.extract_and_check_links(search_url)
                        
                        # Initialize update cells
                        update_cells = []
                        
                        if not doctrine_url:
                            print(f"No doctrine.fr link found for {first_name} {last_name}")
                            # Update the row with empty values and "Not found" URL
                            for idx in specialty_indices:
                                update_cells.append(gspread.Cell(row_idx+1, idx+1, "None"))
                            update_cells.append(gspread.Cell(row_idx+1, serment_index+1, "Not found"))
                            update_cells.append(gspread.Cell(row_idx+1, url_index+1, "Not found"))
                            leads_sheet.update_cells(update_cells)
                            continue
                        
                        print(f"Found doctrine.fr link: {doctrine_url}")
                        
                        # Extract specialties and oath date using specialty_extractor
                        lawyer_id = re.search(r'avocat/([A-Z0-9]+)', doctrine_url)
                        if not lawyer_id:
                            print(f"Could not extract lawyer ID from URL: {doctrine_url}")
                            # Update with empty values but save the URL
                            for idx in specialty_indices:
                                update_cells.append(gspread.Cell(row_idx+1, idx+1, "None"))
                            update_cells.append(gspread.Cell(row_idx+1, serment_index+1, "Not found"))
                            update_cells.append(gspread.Cell(row_idx+1, url_index+1, doctrine_url))
                            leads_sheet.update_cells(update_cells)
                            continue
                            
                        lawyer_id = lawyer_id.group(1)
                        
                        try:
                            # Extract specialties and oath date
                            specialties, oath_date = specialty_extractor.extract_lawyer_data(lawyer_id)
                            
                            # Update specialties (up to 5)
                            for i, idx in enumerate(specialty_indices):
                                specialty_value = "None"
                                if specialties and i < len(specialties):
                                    specialty_value = specialties[i]
                                update_cells.append(gspread.Cell(row_idx+1, idx+1, specialty_value))
                            
                            # Update oath date (use "Not found" if empty)
                            oath_date = oath_date if oath_date else "Not found"
                            update_cells.append(gspread.Cell(row_idx+1, serment_index+1, oath_date))
                            
                        except Exception as e:
                            print(f"Error extracting data for {first_name} {last_name}: {str(e)}")
                            # Update with empty values if extraction fails
                            for idx in specialty_indices:
                                update_cells.append(gspread.Cell(row_idx+1, idx+1, "None"))
                            update_cells.append(gspread.Cell(row_idx+1, serment_index+1, "Not found"))
                        
                        # Always update the URL if we found one
                        update_cells.append(gspread.Cell(row_idx+1, url_index+1, doctrine_url))
                        
                        # Update the sheet
                        leads_sheet.update_cells(update_cells)
                        
                        print(f"Successfully processed {first_name} {last_name}")
                        time.sleep(2)  # Small delay between processing
                        
                    except Exception as e:
                        error_message = str(e)
                        print(f"Error processing row {row_idx+1}: {error_message}")
                        continue
                
                # Wait before checking for new leads
                print(f"Waiting {self.delay} seconds before checking for new leads...")
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