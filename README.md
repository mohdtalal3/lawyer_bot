# Lawyer Data Extractor

This application extracts lawyer specialties and oath dates from doctrine.fr based on Google Sheet data.

## Features

### Smart Processing
- **Resume Capability**: If you stop and restart the bot, it continues from where it left off
- **Selective Processing**: Only processes rows that haven't been successfully scraped yet
- **Auto-Retry**: Automatically retries failed URLs until valid data is found
- **Intelligent URL Validation**: 
  - Skips rows with valid doctrine.fr lawyer profile URLs
  - Retries rows with invalid, empty, or "Not found" URLs
  - Continues trying until a valid lawyer profile is found

### Data Handling
- **Specialty Handling**:
  - Extracts up to 5 specialties for each lawyer
  - Marks as "None" if no specialties are found
  - Preserves found specialties even if some are missing
- **Oath Date Extraction**:
  - Extracts oath date ("Serment") when available
  - Marks as "Not found" if date isn't available
- **URL Management**:
  - Saves valid doctrine.fr URLs
  - Marks as "Not found" if no valid URL is found
  - Updates URLs if better matches are found

### Error Handling
- **Robust Error Recovery**:
  - Handles network errors gracefully
  - Continues processing other rows if one fails
  - Maintains data integrity during errors
- **Data Validation**:
  - Verifies required fields (First Name, Last Name, City)
  - Validates URLs before processing
  - Ensures all required columns exist

## Requirements

- Python 3.7+
- Google Sheets API credentials (JSON file)
- Session cookie from doctrine.fr
- Google Sheet with the following columns:
  - NomBarreau
  - CITY
  - Last Name
  - First Name
  - Company Name
  - cbSiretSiren
  - cbAdresse1
  - cbAdresse2
  - cbCp
  - avLang
  - Email
  - Website
  - Phone
  - speciality 1
  - speciality 2
  - speciality 3
  - speciality 4
  - speciality 5
  - Serment
  - doctrineURL

## Installation

### Setting Up a Virtual Environment (Recommended)

#### First Time Setup:

1. Clone this repository
2. Create a virtual environment:

```bash
# For Windows
python -m venv venv

# For macOS/Linux
python3 -m venv venv
```

3. Activate the virtual environment:

```bash
# For Windows
venv\Scripts\activate

# For macOS/Linux
source venv/bin/activate
```

4. Install the required dependencies:

```bash
pip3 install -r requirements.txt
```

5. Place your Google Sheets API credentials file in the same directory as the script and name it `credentials.json`

6. Create a file named `session_cookie.txt` and paste your doctrine.fr session cookie in it

#### Each Time You Open a New Terminal:

Activate the virtual environment before running the script:

```bash
# For Windows
venv\Scripts\activate

# For macOS/Linux
source venv/bin/activate
```

## Usage

1. Make sure your virtual environment is activated
2. Run the script:

```bash
python run_bot.py
```

3. When prompted:
   - Enter your Google Sheet ID (required)
   - Enter sheet name (press Enter for default 'FRANCE: 78000 lawyers')
   - Enter check interval in seconds (press Enter for default 5)

4. The bot will:
   - Start processing unprocessed rows
   - Skip rows that already have valid doctrine.fr URLs
   - Update rows that have invalid or missing data
   - Continue running until stopped with Ctrl+C

### Example Session:
```
Starting Lawyer Data Extractor...
Using credentials from: credentials.json
Enter Google Sheet ID (required): your_sheet_id_here
Enter Sheet Name (press Enter for default 'FRANCE: 78000 lawyers'): [Press Enter]
Enter check interval in seconds (press Enter for default 5): [Press Enter]

Starting with following settings:
Sheet ID: your_sheet_id_here
Sheet Name: FRANCE: 78000 lawyers
Check Interval: 5 seconds

Press Ctrl+C to stop the process
```

## Getting Your Session Cookie

1. Log in to doctrine.fr in your browser
2. Open Developer Tools (F12 or right-click > Inspect)
3. Go to the Application tab
4. Under Storage, select Cookies > https://www.doctrine.fr
5. Find the "session" cookie
6. Copy the value and paste it into the `session_cookie.txt` file

## Session Cookie Management

- If you see an error message about the session cookie expiring, you'll need to:
  1. Log in to doctrine.fr again
  2. Get a fresh session cookie following the steps above
  3. Update the `session_cookie.txt` file with the new cookie
  4. The bot will automatically detect the updated cookie and continue processing
  5. Press y to continue
## Data Processing Logic

1. **URL Processing**:
   - Empty URL → Process row
   - "Not found" URL → Process row
   - Invalid URL → Process row
   - Valid doctrine.fr lawyer URL → Skip row

2. **Data Extraction**:
   - Found valid URL → Extract specialties and oath date
   - No specialties found → Save URL and date, mark specialties as "None"
   - No oath date found → Save URL and specialties, mark date as "Not found"
   - Nothing found → Mark everything as "Not found" or "None"

3. **Auto-Retry Logic**:
   - Failed searches are automatically retried in next cycle
   - Invalid URLs are replaced if better ones are found
   - Processing continues until valid data is found or explicitly marked as not found

## Troubleshooting

- Make sure your Google Sheet has the correct column names exactly as specified
- Ensure your service account has edit access to the Google Sheet
- Check that credentials.json is in the same directory as the script
- Verify that your session_cookie.txt file contains a valid session cookie
- Look for error messages in the console output 