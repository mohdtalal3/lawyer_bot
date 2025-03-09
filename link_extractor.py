from requests_html import HTMLSession
import os
import time

def extract_and_check_links(url):
    """
    Extract links from a Bing search result and find the first doctrine.fr link
    
    Args:
        url (str): The Bing search URL
        
    Returns:
        str or None: The first doctrine.fr link found, or None if no link is found
    """
    try:
        session = HTMLSession()
        response = session.get(url)
        
        # Try to render the JavaScript content
        try:
            response.html.render(timeout=30)
        except Exception as e:
            print(f"Error rendering page: {str(e)}")
            # Continue with the HTML we have
        
        # Try different XPath patterns to find links
        links = []
        
        # Pattern 1: Standard Bing search results
        links.extend(response.html.xpath("//div[@class='b_tpcn']//a[@class='tilk']/@href"))
        
        # Pattern 2: Alternative Bing search results
        if not links:
            links.extend(response.html.xpath("//li[@class='b_algo']//a/@href"))
            
        # Pattern 3: More generic approach
        if not links:
            links.extend(response.html.xpath("//a[contains(@href, 'doctrine.fr')]/@href"))
        
        # Check for doctrine.fr links
        for link in links:
            if "https://www.doctrine.fr/" in link:
                # Check if it's a lawyer profile
                if "/p/avocat/" in link:
                    return link
        
        # If no lawyer profile found, return any doctrine.fr link
        # for link in links:
        #     if "https://www.doctrine.fr/" in link:
        #         return link
                
        return None
        
    except Exception as e:
        print(f"Error extracting links: {str(e)}")
        return None
    finally:
        session.close()
if __name__ == "__main__":
    # Example usage
    url_to_check = "https://www.bing.com/search?q=Aur%C3%A9lia+BADY+AGEN+doctrine.fr"
    matching_link = extract_and_check_links(url_to_check)
    if matching_link:
        print("Matching link found:", matching_link)
    else:
        print("No matching link found.")