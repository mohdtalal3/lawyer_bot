import requests
import json
import re
import pandas as pd
import os

def extract_data(data):
    try:
        # Extract subcategories with their counts
        subcategories = []
        for domain in data.get('domains', []):
            for sub in domain.get('sub', []):
                subcategories.append({
                    'Subcategory': sub['categoryName'], 
                    'Count': sub['count']
                })
        
        # If no subcategories found, return empty DataFrame
        if not subcategories:
            return pd.DataFrame(columns=['Subcategory', 'Count'])
        
        # Convert to DataFrame
        df = pd.DataFrame(subcategories)
        
        # Sort by count in descending order and select the top 5
        top_subcategories = df.sort_values(by='Count', ascending=False).head(5)
        return top_subcategories
    except Exception as e:
        print(f"Error extracting specialties: {str(e)}")
        return pd.DataFrame(columns=['Subcategory', 'Count'])

def extract_lawyer_data(lawyer_id):
    """
    Extract lawyer specialties and oath date from doctrine.fr
    
    Args:
        lawyer_id (str): The lawyer ID from the doctrine.fr URL
        
    Returns:
        tuple: (list of specialties, oath date, error_type or None)
    """
    # URL for the lawyer page
    url_lawyer_page = f"https://www.doctrine.fr/p/avocat/{lawyer_id}"

    # Headers for the first request
    headers_first = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Referer": "https://www.doctrine.fr",
        "Upgrade-Insecure-Requests": "1"
    }

    # Read session cookie from file
    cookies_first = {}
    try:
        cookie_file = "session_cookie.txt"
        if not os.path.exists(cookie_file):
            print(f"Error: {cookie_file} not found. Please create this file with your session cookie.")
            return [], "Not found", "cookie_missing"
            
        with open(cookie_file, "r") as f:
            session_cookie = f.read().strip()
            if not session_cookie:
                print(f"Error: {cookie_file} is empty. Please add your session cookie to this file.")
                return [], "Not found", "cookie_empty"
            cookies_first = {"session": session_cookie}
    except Exception as e:
        print(f"Error reading session cookie: {str(e)}")
        return [], "Not found", "cookie_error"

    # Create a session
    session = requests.Session()
    session.headers.update(headers_first)
    session.cookies.update(cookies_first)

    # Send GET request to lawyer page
    response_first = session.get(url_lawyer_page)

    # Default values
    specialties = []
    oath_date = "Not found"

    if response_first.status_code == 200:
        # Extract JSON from the response HTML using regex
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response_first.text, re.DOTALL)
        
        if match:
            json_data = match.group(1)
            data = json.loads(json_data)  # Convert to Python dictionary

            try:
                # Extract `readKey` and `summary`
                read_key = data["props"]["pageProps"]["readKey"]
                summary = data["props"]["pageProps"]["lawyerInfos"]["summary"]

                # Extract oath date
                oath_date_match = re.search(r"prêté serment le (\d{1,2} \w+ \d{4})|(\d{1,2} \w+ \d{4})", summary)
                if oath_date_match:
                    oath_date = oath_date_match.group(1) if oath_date_match.group(1) else oath_date_match.group(2)

                # Second request to get decisions data
                url_decisions = f"https://www.doctrine.fr/api/v2/lawyers/{lawyer_id}/decisions"

                # Headers for the second request
                headers_second = {
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                    "Content-Type": "application/json",
                    "Referer": f"https://www.doctrine.fr/p/avocat/{lawyer_id}",
                    "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin"
                }

                # Parameters for the second request
                params = {
                    "read_key": read_key
                }

                # Update session with new headers
                session.headers.update(headers_second)

                # Send GET request for decisions
                response_second = session.get(url_decisions, params=params)

                if response_second.status_code == 200:
                    decisions_data = response_second.json()
                    top_subcategories = extract_data(decisions_data)
                    
                    # Convert top specialties to a list
                    specialties = top_subcategories['Subcategory'].tolist()
            except KeyError as e:
                error_msg = str(e)
                print(f"Error extracting data: {error_msg}. The page structure may have changed.")
                if "readKey" in error_msg:
                    return [], "Not found", "readKey"
                return [], "Not found", "data_error"
    session.close()
    return specialties, oath_date, None

def main():
    # Example usage
    lawyer_id = "LAF40A920BF17CFD162A4"
    specialties, oath_date, error = extract_lawyer_data(lawyer_id)
    
    if error:
        print(f"Error: {error}")
    else:
        print("\n📊 Top 5 Specialties:")
        print(specialties)
        print(f"📅 Oath Date: {oath_date}")

if __name__ == "__main__":
    main()