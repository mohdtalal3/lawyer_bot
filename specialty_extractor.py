import requests
import json
import re
import pandas as pd
import os
import sys
import time
import asyncio
from pydoll.browser.chrome import Chrome
from pydoll.browser.options import Options
from pydoll.constants import By
import os

def solve_captcha(url):
    user_data_dir = os.path.join(os.getcwd(), 'user_data')
    options = Options()
    options.add_argument(f'--user-data-dir={user_data_dir}')
    extension_dir = os.path.join(os.getcwd(), 'extension')
    options.add_argument(f'--load-extension={extension_dir}')
    
    async def main():
        async with Chrome(options=options) as browser:
            await browser.start()
            page = await browser.get_page()
            await page.go_to(url)
            # time.sleep(10)
            # # Wait for the captcha button to be clickable using CSS Selector
            # button = await page.find_element(By.CSS_SELECTOR, "button.SignupCaptcha_accessButton__RCz8B[type='button']")
            # # Click the captcha button
            # await button.click()
            # # Wait for some time to ensure the captcha is solved
            time.sleep(30)
    
    asyncio.run(main())



def get_lawyer_id(session, first_name, last_name, city):
    """
    Extract lawyer ID and oath date directly from doctrine.fr API using existing session
    """
    # Base URL for the API
    base_url = "https://www.doctrine.fr/api/v2/search"

    # Parameters for the search
    params = {
        "q": f"{first_name} {last_name} {city}",
        "chrono": "false",
        "sort_nbr_commentaire": "false",
        "chrono_inverted": "false",
        "sort_alphanumeric": "false",
        "from": 0,
        "size": 5,
        "type": "lawyer",
        "only_top_results": "true",
        "exclude_moyens": "false",
    }

    # Headers for search
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }

    session.headers.update(headers)

    try:
        response = session.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", [])
            if hits:  # Check if there's at least one result
                lawyer_id = hits[0].get("id")
                oath_date = hits[0].get("sermentDate", "Not found")
                return lawyer_id, oath_date
        elif response.status_code == 404:
            print(f"Lawyer not found: {first_name} {last_name} in {city}")
        else:
            print(f"API request failed with status code {response.status_code}")
            
    except Exception as e:
        print(f"Error searching for lawyer: {str(e)}")
    
    return None, "Not found"

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

def extract_lawyer_data(first_name, last_name, city):
    """
    Extract lawyer specialties and oath date from doctrine.fr
    """
    # Create a session for all requests
    session = requests.Session()
    retry_count = 0
    max_retries = 5
    delay = 120  # Fixed 2 minutes delay
    
    # Read session cookie from file
    try:
        cookie_file = "session_cookie.txt"
        if not os.path.exists(cookie_file):
            print(f"Error: {cookie_file} not found.")
            return [], "Not found", None
            
        with open(cookie_file, "r") as f:
            session_cookie = f.read().strip()
            if not session_cookie:
                print(f"Error: {cookie_file} is empty.")
                return [], "Not found", None
            session.cookies.update({"session": session_cookie})
    except Exception as e:
        print(f"Error reading session cookie: {str(e)}")
        return [], "Not found", None

    # Get lawyer ID and oath date from API
    lawyer_id, oath_date = get_lawyer_id(session, first_name, last_name, city)
    if not lawyer_id:
        print(f"Could not find lawyer ID for {first_name} {last_name} in {city}")
        return [], "Not found", None
    if oath_date=="Not found":
        print("No Oath Date")
        return [], "Not found", None
    # URL for the lawyer page
    url_lawyer_page = f"https://www.doctrine.fr/p/avocat/{lawyer_id}"
    print(f"URL for the lawyer page: {url_lawyer_page}")

    while retry_count < max_retries:
        try:
            # Headers for lawyer page
            headers_first = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "Referer": "https://www.doctrine.fr",
                "Upgrade-Insecure-Requests": "1"
            }

            session.headers.update(headers_first)
            response_first = session.get(url_lawyer_page)

            if response_first.status_code == 404:
                print(f"Lawyer page not found: {url_lawyer_page}")
                return [], "Not found", None
            elif response_first.status_code in [429, 403]:
                retry_count += 1
                print(f"\n⚠️ Rate limit detected! Waiting {delay} seconds before retry {retry_count}/{max_retries}")
                time.sleep(delay)
                continue
            elif response_first.status_code != 200:
                print(f"Failed with status code {response_first.status_code}")
                return [], "Not found", None
            if response_first.status_code == 200:
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response_first.text, re.DOTALL)
                
                if match:
                    try:
                        json_data = match.group(1)
                        data = json.loads(json_data)
                        read_key = data["props"]["pageProps"]["readKey"]

                        # Get specialties
                        headers_second = {
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "Referer": url_lawyer_page,
                        }
                        session.headers.update(headers_second)
                        
                        url_decisions = f"https://www.doctrine.fr/api/v2/lawyers/{lawyer_id}/decisions"
                        response_second = session.get(url_decisions, params={"read_key": read_key})

                        if response_second.status_code == 200:
                            decisions_data = response_second.json()
                            top_subcategories = extract_data(decisions_data)
                            specialties = top_subcategories['Subcategory'].tolist()
                            if not specialties:
                                specialties = ["None"] * 5
                            session.close()
                            return specialties, oath_date, url_lawyer_page

                    except KeyError as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            print("\n⚠️ CAPTCHA detected after maximum retries! Stopping the process.")
                            sys.exit(1)
                        print(f"\n⚠️ Access denied! Setting pause for all threads...")
                        print("Please solve the CAPTCHA")
                        print("Solving Captcha", url_lawyer_page)
                        solve_captcha(url_lawyer_page)
                        continue

            print(f"Failed with status code {response_first.status_code}")
            return [], "Not found", None

        except Exception as e:
            print(f"Error processing request: {str(e)}")
            retry_count += 1
            if retry_count >= max_retries:
                break
            print(f"\n⚠️ Error occurred! Waiting {delay} seconds before retry {retry_count}/{max_retries}")
            time.sleep(delay)

    session.close()
    return [], "Not found", None

def main():
    # Example usage
    first_name = "Charles"
    last_name = "ZWILLER"
    city = "MONTPELLIER"
    
    specialties, oath_date, error = extract_lawyer_data(first_name, last_name, city)
    
    if error:
        print(f"Error: {error}")
    else:
        print("\n📊 Top 5 Specialties:")
        print(specialties)
        print(f"📅 Oath Date: {oath_date}")

if __name__ == "__main__":
    main()