import requests
import json
import re
import pandas as pd

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
        tuple: (list of specialties, oath date)
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

    # Cookies for the first request
    # cookies_first = {
    #     "session": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwiaWF0IjoxNzQxMDg2OTc2LCJ1YXQiOjE3NDEwODg0NDAsImV4cCI6MTc0ODk5Njk3Nn0..Cg9_gaKBxqRC0KvJ.4ZwZdKJOnDkYXepCFI2ER3OmY3UCj1R1Hr5ppehFIU9rlBLYRL3IYIcr2fLauG5ZuMBUSk4sJ8VnVcdGLrtOQaj9WeZE1JQ5KxonLRVav_z-V22FSdJnvICHiuAqnw9tVWcQefMYn_K3y70JXCNMIkXLvPRSzowoLj23yJfcif7aycuE8aExi7opP_5hFUdKQM2m7eh-dsaApQIo7tEyS810y_ccwIvpXlkRIGxPRJkK3JFPnOC-vRgfUXViGRK3fVkraVh78XJ24t-iq6PhmbjD-yIn7fMSvSC2dX4YGOlfKh6Rzi1xfngBnA8EGgmmOvrcStuHBUSXXrGvwkw09W7lAiVbL2ILWdTX8f-qUU189T-MzWykZkiPMQG2-JhdJxZR5FoYMNoVKgepPJd2RSzH69GweUCCZvLiKNAeGt2M2B9aAShjCd5dYJtyY5WRSG-IDsqwx9gHy53P7ghWBpxJYSYnu2T1LcK4d3lLS0ZJte0DlfPQZU2ppA08QR5cLru8xQGXmguy7yRNjeX8bBdsw-OGN6FJlFmZ43d0wk9Zg940gNMkpmduYoYV0yVq176l19uXcVjydVA6yB7D5WXuJUTNQ41h2ezXIQkkSdAah67Ya8IEjZbm4G_lFJBkIOQWTbsVZcrTlcGqiIui13jARW2NkEro4kKW8QUs2BZ5D8i-r_EmGJk05sEJ44lw6xlQu_sI-SlcZIfVWoKU28N5BrHqyXoBZDezO7QhaN366YF7ZuexHhlSaR0agubks26RCXk-jfSkpFwjleXuc-NTVa5YNAUskWxewm23JyBfLSYsGkP4PI0y9bListYuxuPZnYhob__dJPoUHEQstCZRRpbSe6w_JAG9_HDJQMcXniFJnMxPHiLDEOI9IgxlFMhbOXHfd9FctoKF1E8772KsUdnk7_MzRC0sv4ivpH9sIfJm9oGxhVZC5ztlAzb4nzLlqXwg_VDzxlsY31EqTFUxtedNoI1OzsK0vYUpsvIltrf1O1XH3ftm2D-tVGaswdBQOR9hXznQL0vx7_WA6pms7al1tjVIji2A-kzRiJgEBXMe7RPPz8WePMW0vXYVFKpRjLzBOtZsgW99MK9dCK__oPSq1rNW-YkKO75o8Ba4o3tNQ2-xKBOKpKxTsszqEdQ_jTRJvn53Xfx44LroIxQRh7-O2GftOzaok4FEXpHnQoLI8FScgAYhrF4ttdMGDUq06H-2uAZk1ukQ0748jWz5Yq6ZK9KQuo5elEczk3hgGxukCQ7IWj2aDW3_3LZjtc8CcF1_Gt89Hbio9pQ7ym4nTRSODaRME3mtF_O1TxX0SHPC5KZ41jy7dhN_gCRBxVGrC_xwM9MShSwImmPThvnSddtciDgyS9BUtj8lScdf_a6ovGVJ5yiHlRjz3KxrKXmReT2k3GkAMA8Zfi54aXquJ_ONZts3IaIZ4PlcegOe-Gm8SqPfXKtO4CcR5rmTfvFDJCBmp6J4TMdNVeEIUQQfDxOWVU7q5tWgqrcXoZNI3ZsHl_t71916YEZC5Ml7u7KDW71YvvggpADTQIlL4foXUbSNyTOPL_hLDhi3SdCXneejWxlUKerhLRnDSMPvg2IZRk3UKkUM45oAZhcIlTyxvsxMIEwjTrcDIRoTDyFqUh8_I4jrgLcp6rxjUgBQ7ZEQT83LpsP_Bel9g_AsBGzvTzdqmuuKanF8HtSoSLBGUW6m-oPpTS0ODlaK_A8rNyQhoKlFj0vkufix7megxjzl8Am63bQuwAkivo_Q5zltzlPflKcASgULRWxNTACpf2qFFZxPGosT1AVcckvPSm05UNo5IK_dTN5XAsy06iqiRrSuJDD2ErJov25dwjZ1rM4OoGABu61qpdYbqGFArhvysw4TYTrUq9o9wrdk4ly37BxNbb1o_d-4vyFGKELEWgVqIenEmXWC8RGPaTFL-HS7yhQl8bJMuFpTD_30WZHwk1wJGSQiBV-Yjp-eXRZXSvmJtro6KQQdu6JNDaCuBxtdqx8M7Sq8kMthmj7B4XAvXCDKPrDGO-jQ82qFRZOHt83jNll8qbYztC8dWdZ18Pzd_gp43W5qNJWyxYwBBbuDn1rtBcoqpJQLsFdIHJgDqb6oUN7yIMRuYI9dGKpeJT0eN8draONPzZohyJjSTRpBM0v6JUXDaJh5e4aAlBAESiP-e17BmOoanOLMBnPZBP14nw_tM3hligV7IU_egxSMKmCsufXYBPakowuGnWUpKutGv1YbZymyN8K3BZE_BrkK8Gj9EXTMti7G7cjBvBxh0OmM37t_RiMLhZ4p-5GOynShLr1w2svSahvnB0iOr5T1PtVMa9LH61EBhZaRNWfGL0Gqi8uDFe2m448D4jH9TNil4QJuYLO2iixIeWkjfl3nyR0cKpiXrbNTJ_PgsJF2GisdRrADty8ckL6raEnbWm0tpHSi0tjg2OOn4-ADNydXVVJJcHYrm9mjVfCSv63mOLfFrdYXlClhzj3-s5RgXJXBNK7TJzNEK40qr2FXbT85_eD5czfTDlYHmjBPaoUSNwbQtZbyXpLZ0RWnPHlwoEFg2OjSP1k-7F9BWEd7RI_GyYS78RLKCpcTHcCoKLlcDd49kaGvglPdNayFpWh0t5uxlR0GqTD7QLZe1zp013dCNf8zd6I3ee7aXDXewzNiTFSNKYdh4lWec4-U4tWBERSTnu07GOAWbZlu1JEBWVTobLOr42u7ta-odvMuqibXMGidf2C-vdyr3IYFnV7TUJ9vAJderUu3kLIfZ5bSQWvCEm8qgPNs3ChQkKLbfWWorodonGkpsYu7HyCJIIT6zMgUW7_GRTp_Da0J4plHKkyFWNzVvpDVDfPsYMTt4FI8jQJ4nsurXWllKUyLntHhx7XJcSrCYG0wwjfGnwVpa-NhWFd57qO9rDJDLNXshr6Z5i_eEH6SxJNciZMsWXE6IBOlWIylyTrASQAZGMe3Domv7M88kM2nCorpTTnU_vcqxfwVBClFWH43XJ6HKiozDjPKp8IdwPXAjem7JUckOVZhDTJCh5HfIlEh_qb-FJrTesmm6OsHJRG4DSvRUhB2t1etd-qXKhUxWJux2Fz8CdyaaDq6Q55ZDbA49dDXSurV-GDPQ7mdHT2xzLZGxrLRPMtyH8BeSEZQ62fu3Zo9YZqlCQSaW00SiWLdRfOzB3Jwqq3NiKVRvDhZvUcsA8MEBQI0hgNy_50m-bA68WymiZ7QnLgYGmnYim7yNLDU65N2j_h11Qh8ujrbQFlF11eesOpQdnnVrZDlhXYlRxr6lrdQGc62ehen-ru8g_RuBGBJVgmnpGub17LocABx9SAAKXMAqESBiD4X0uRXuRupbeFqIRawIcqZQIZHb4i46eyk3t5WktmY57eghSLFppjrDm7QtCj9Sc54_3oVhj-nPQaM1VmjGT0HyIRvPFyNBAlrNEjEJxCskGt3fcgXgIK7lHlxlkPnnYFGGFzNsfataE5Y5jwKEHeB.QJtyZS4mNdmFf2mH5Wesag",
    # }

    # Create a session
    session = requests.Session()
    session.headers.update(headers_first)
    #session.cookies.update(cookies_first)

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
    session.close()
    return specialties, oath_date

def main():
    # Example usage
    lawyer_id = "LAF40A920BF17CFD162A4"
    specialties, oath_date = extract_lawyer_data(lawyer_id)
    
    print("\n📊 Top 5 Specialties:")
    print(specialties)
    print(f"📅 Oath Date: {oath_date}")

if __name__ == "__main__":
    main()