from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time


class WhoisScraper:
    def __init__(self, headless=False):
        """Initialize the WhoisScraper with Chrome WebDriver."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def search_domain(self, domain):
        """
        Search for a domain on whois.com
        
        Args:
            domain (str): The domain name or IP address to search
        """
        try:
            # Navigate to who.is
            print(f"Navigating to who.is...")
            self.driver.get("https://who.is/")
            
            # Wait for the search input to be present
            search_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            # Clear any existing text and enter the domain
            print(f"Searching for domain: {domain}")
            search_input.clear()
            search_input.send_keys(domain)
            
            # Press Enter to search
            search_input.send_keys(Keys.RETURN)
            
            # Wait for results page to load
            print("Waiting for results page to load...")
            time.sleep(3)  # Give the page time to load
            
            return True
        except Exception as e:
            print(f"Error during search: {e}")
            return False
    
    def scrape_whois_data(self):
        """
        Scrape WHOIS data from the results page.
        
        Returns:
            dict: Dictionary containing all scraped data
        """
        try:
            data = {
                'domain_info': {},
                'important_dates': {},
                'domain_status': []
            }
            
            # Wait for the main content to load
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "bg-gray-50"))
            )
            
            # Scrape domain information (header section)
            print("Scraping domain information...")
            domain_header = self.driver.find_element(By.CSS_SELECTOR, ".bg-gray-50.rounded-lg.shadow-sm.p-6.mb-8")
            
            # Domain name
            domain_name_elem = domain_header.find_element(By.TAG_NAME, "h1")
            data['domain_info']['domain_name'] = domain_name_elem.text
            
            # IP Address
            try:
                ip_elem = domain_header.find_element(By.CSS_SELECTOR, "p.text-gray-600:nth-of-type(2)")
                ip_text = ip_elem.text
                if "IP Address:" in ip_text:
                    ip_link = ip_elem.find_element(By.TAG_NAME, "a")
                    data['domain_info']['ip_address'] = ip_link.text
            except Exception as e:
                print(f"Could not find IP address: {e}")
                data['domain_info']['ip_address'] = "N/A"
            
            # Scrape Important Dates
            print("Scraping important dates...")
            try:
                dates_section = self.driver.find_element(By.XPATH, "//h2[text()='Important Dates']/parent::div")
                date_items = dates_section.find_elements(By.CSS_SELECTOR, "dl > div")
                
                for item in date_items:
                    dt = item.find_element(By.TAG_NAME, "dt").text
                    dd = item.find_element(By.TAG_NAME, "dd").text
                    data['important_dates'][dt.lower()] = dd
            except Exception as e:
                print(f"Error scraping dates: {e}")
            
            # Scrape Domain Status
            print("Scraping domain status...")
            try:
                status_section = self.driver.find_element(By.XPATH, "//h2[text()='Domain Status']/parent::div")
                status_items = status_section.find_elements(By.CSS_SELECTOR, "ul li")
                
                for item in status_items:
                    status_text = item.text.strip()
                    if status_text:
                        data['domain_status'].append(status_text)
            except Exception as e:
                print(f"Error scraping domain status: {e}")
            
            return data
            
        except Exception as e:
            print(f"Error scraping data: {e}")
            return None
    
    def get_whois_info(self, domain):
        """
        Main method to get WHOIS information for a domain.
        
        Args:
            domain (str): The domain name or IP address
            
        Returns:
            dict: Dictionary containing all scraped WHOIS data
        """
        try:
            # Search for the domain
            if not self.search_domain(domain):
                return None
            
            # Scrape the data
            data = self.scrape_whois_data()
            
            return data
            
        except Exception as e:
            print(f"Error getting WHOIS info: {e}")
            return None
        finally:
            # Optional: Keep browser open for debugging
            # self.close()
            pass
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            print("Browser closed.")


def get_domain_whois_info(domain, headless=True):
    """
    Standalone function to get WHOIS information for a domain.
    
    Args:
        domain (str): The domain name or IP address
        headless (bool): Whether to run browser in headless mode (default: True)
    
    Returns:
        dict: Dictionary containing WHOIS data or None if failed
    """
    scraper = None
    try:
        scraper = WhoisScraper(headless=headless)
        data = scraper.get_whois_info(domain)
        return data
    except Exception as e:
        print(f"Error in get_domain_whois_info: {e}")
        return None
    finally:
        if scraper:
            scraper.close()


def print_whois_data(data):
    """Pretty print the WHOIS data."""
    if not data:
        print("No data to display")
        return
    
    print("\n" + "="*60)
    print("WHOIS INFORMATION")
    print("="*60)
    
    # Domain Info
    print("\n--- Domain Information ---")
    for key, value in data['domain_info'].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Important Dates
    print("\n--- Important Dates ---")
    for key, value in data['important_dates'].items():
        print(f"{key.title()}: {value}")
    
    # Domain Status
    print("\n--- Domain Status ---")
    for i, status in enumerate(data['domain_status'], 1):
        print(f"{i}. {status}")
    
    print("="*60 + "\n")


# Example usage
if __name__ == "__main__":
    # Example: Scrape WHOIS data for zoho.com
    domain_to_search = input("Enter domain name or IP address: ").strip()
    
    if not domain_to_search:
        domain_to_search = "zoho.com"  # Default example
    
    print(f"\nStarting WHOIS lookup for: {domain_to_search}\n")
    
    # Create scraper instance
    scraper = WhoisScraper(headless=False)  # Set to True to run without browser window
    
    try:
        # Get WHOIS data
        whois_data = scraper.get_whois_info(domain_to_search)
        
        # Display the data
        if whois_data:
            print_whois_data(whois_data)
        else:
            print("Failed to retrieve WHOIS data")
    
    finally:
        # Close the browser
        input("Press Enter to close the browser...")
        scraper.close()
