#!/usr/bin/env python3
"""
MCA (Ministry of Corporate Affairs) Company Details Automation Agent
Fetches publicly available company information from zaubacorp.com
Uses Selenium with human-like behavior for reliable extraction

ChromeDriver Setup:
- Uses ChromeDriver from system PATH by default
- To specify a custom path, set CHROMEDRIVER_PATH in .env file
- Make sure your ChromeDriver version matches your Chrome browser version
"""

import re
import json
import sys
import time
import os
from typing import Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages missing. Install with:")
    print("pip install selenium beautifulsoup4")
    sys.exit(1)

# Load ChromeDriver path from environment variable (optional)
# If not set, will use system PATH
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "")

class MCAAutomationAgent:
    """Backend automation agent for MCA company details extraction using Selenium"""
    
    # CIN validation regex (21 characters: L/U + 5 digits + State code + Year + Type + 6 digits)
    CIN_PATTERN = r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'
    
    BASE_URL = "https://www.zaubacorp.com"
    
    def __init__(self, headless: bool = False):
        """
        Initialize Selenium WebDriver
        Args:
            headless: Run browser in headless mode (default: False for more reliable behavior)
        """
        self.driver = None
        self.headless = headless
        self._init_driver()
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with human-like configuration"""
        options = Options()
        
        # Human-like browser configuration
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        
        try:
            # Use ChromeDriver path from .env file if specified
            if CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
                # Use specified ChromeDriver path from .env
                service = Service(CHROMEDRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                # Use ChromeDriver from system PATH (your existing installation)
                self.driver = webdriver.Chrome(options=options)
            
            # Remove webdriver property to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except WebDriverException as e:
            raise Exception(f"Failed to initialize Chrome WebDriver: {str(e)}")
    
    def validate_cin(self, cin: str) -> bool:
        """
        Validate CIN format using official regex pattern
        Returns: True if valid, False otherwise
        """
        if not cin or not isinstance(cin, str):
            return False
        return bool(re.match(self.CIN_PATTERN, cin.strip().upper()))
    
    def human_like_typing(self, element, text: str, min_delay: float = 0.05, max_delay: float = 0.15):
        """
        Simulate human-like typing with random delays
        """
        import random
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

    def fetch_company_details(self, company_name: str, mca_number: str) -> Dict[str, Any]:
        """
        Main automation logic to fetch company details using Selenium
        Args:
            company_name: Name of the company
            mca_number: MCA/CIN number
        Returns: Structured JSON response
        """
        company_name = company_name.strip()
        mca_number = mca_number.strip().upper()
        
        # Construct search query: "company name mca number"
        search_query = f"{company_name} {mca_number}"
        
        # Step 1: Validate MCA number format (optional - can search even with invalid format)
        if not self.validate_cin(mca_number):
            print(f"Warning: MCA number '{mca_number}' may not be in standard CIN format", file=sys.stderr)
        
        try:
            # Step 2: Navigate to website
            try:
                self.driver.get(self.BASE_URL)
                wait = WebDriverWait(self.driver, 40)  # Increased timeout to 40 seconds
            except WebDriverException as e:
                return {
                    "source": "zaubacorp.com",
                    "company_name": company_name,
                    "mca_number": mca_number,
                    "search_query": search_query,
                    "error": {
                        "type": "NETWORK_ERROR",
                        "message": f"Failed to load website: {str(e)}"
                    }
                }
            
            # Step 3: Locate search input field and enter search query
            try:
                # Wait for search input field to be present
                search_input = wait.until(
                    EC.presence_of_element_located((By.ID, "searchid"))
                )
                
                # Clear any existing value
                search_input.clear()
                time.sleep(0.5)
                
                # Human-like typing of search query
                self.human_like_typing(search_input, search_query)
                
                # Small delay before pressing Enter
                time.sleep(0.5)
                
                # Submit the search
                search_input.send_keys(Keys.ENTER)
                
            except (TimeoutException, NoSuchElementException) as e:
                return {
                    "source": "zaubacorp.com",
                    "company_name": company_name,
                    "mca_number": mca_number,
                    "search_query": search_query,
                    "error": {
                        "type": "PARSE_ERROR",
                        "message": f"Search input field not found: {str(e)}"
                    }
                }
            
            # Step 4: Wait for results page to load
            try:
                # Wait for the company information table to load
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.table.table-striped"))
                )
                # Additional wait for full render
                time.sleep(3)  # Increased wait time for page to fully render
                
            except TimeoutException:
                # Check if "no record found" message appears
                page_text = self.driver.page_source.lower()
                if any(phrase in page_text for phrase in ['no record found', 'not found', 'invalid']):
                    return {
                        "source": "zaubacorp.com",
                        "company_name": company_name,
                        "mca_number": mca_number,
                        "search_query": search_query,
                        "error": {
                            "type": "NOT_FOUND",
                            "message": f"No company record found for '{search_query}'"
                        }
                    }
                
                return {
                    "source": "zaubacorp.com",
                    "company_name": company_name,
                    "mca_number": mca_number,
                    "search_query": search_query,
                    "error": {
                        "type": "PARSE_ERROR",
                        "message": "Company information table did not load within timeout period"
                    }
                }
            
            # Step 5: Parse HTML response
            html = self.driver.page_source
            return self.parse_response(html, company_name, mca_number, search_query)
            
        except Exception as e:
            return {
                "source": "zaubacorp.com",
                "company_name": company_name,
                "mca_number": mca_number,
                "search_query": search_query,
                "error": {
                    "type": "PARSE_ERROR",
                    "message": f"Unexpected error: {str(e)}"
                }
            }
    
    def parse_response(self, html: str, company_name: str, mca_number: str, search_query: str) -> Dict[str, Any]:
        """
        Parse HTML response and extract company details from table
        Args:
            html: HTML content to parse
            company_name: Name of the company searched
            mca_number: MCA/CIN number searched
            search_query: Full search query used
        Returns: Structured JSON response
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for "no record found" or similar messages
        page_text = soup.get_text().lower()
        if any(phrase in page_text for phrase in ['no record found', 'not found', 'invalid cin']):
            return {
                "source": "zaubacorp.com",
                "company_name": company_name,
                "mca_number": mca_number,
                "search_query": search_query,
                "error": {
                    "type": "NOT_FOUND",
                    "message": f"No company record found for '{search_query}'"
                }
            }
        
        # Locate the company information table
        table = soup.find('table', class_='table table-striped')
        
        if not table:
            return {
                "source": "zaubacorp.com",
                "company_name": company_name,
                "mca_number": mca_number,
                "search_query": search_query,
                "error": {
                    "type": "PARSE_ERROR",
                    "message": "Company information table not found in response"
                }
            }
        
        # Extract data from table rows
        company_info = {}
        tbody = table.find('tbody')
        
        if not tbody:
            return {
                "source": "zaubacorp.com",
                "company_name": company_name,
                "mca_number": mca_number,
                "search_query": search_query,
                "error": {
                    "type": "PARSE_ERROR",
                    "message": "Table body not found"
                }
            }
        
        rows = tbody.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].text.strip()
                value_cell = cells[1]
                
                # Check if this is the Activity field with NIC Code
                if key == "Activity" or "Activity" in key:
                    # Extract NIC Code and Description separately
                    spans = value_cell.find_all('span', class_='tdsp')
                    nic_info = {}
                    
                    for span in spans:
                        text = span.text.strip()
                        if 'NIC Code:' in text:
                            nic_info['NIC Code'] = text.replace('NIC Code:', '').strip()
                        elif 'NIC Description:' in text:
                            nic_info['NIC Description'] = text.replace('NIC Description:', '').strip()
                    
                    if nic_info:
                        company_info[key] = nic_info
                    else:
                        company_info[key] = value_cell.text.strip()
                else:
                    # Regular field - just get the text
                    value = value_cell.text.strip()
                    # Clean up extra whitespace
                    value = ' '.join(value.split())
                    company_info[key] = value
        
        if not company_info:
            return {
                "source": "zaubacorp.com",
                "company_name": company_name,
                "mca_number": mca_number,
                "search_query": search_query,
                "error": {
                    "type": "PARSE_ERROR",
                    "message": "No data extracted from table"
                }
            }
        
        # Return successful response with extracted data
        return {
            "source": "zaubacorp.com",
            "company_name": company_name,
            "mca_number": mca_number,
            "search_query": search_query,
            "data": company_info
        }
    
    def close(self):
        """Close the WebDriver and cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass

def main():
    """
    Command-line interface for the automation agent
    Usage: python mca.py "<company_name>" <mca_number> [--headless]
    """
    if len(sys.argv) < 3:
        print("Usage: python mca.py \"<company_name>\" <mca_number> [--headless]", file=sys.stderr)
        print("Example: python mca.py \"Zoho Corporation\" U72900KA2018PTC123456", file=sys.stderr)
        print("Example: python mca.py \"Zoho Corporation\" U72900KA2018PTC123456 --headless", file=sys.stderr)
        print("\nNote: Company name should be in quotes if it contains spaces", file=sys.stderr)
        sys.exit(1)
    
    company_name = sys.argv[1]
    mca_number = sys.argv[2]
    headless = '--headless' in sys.argv
    
    agent = None
    try:
        agent = MCAAutomationAgent(headless=headless)
        result = agent.fetch_company_details(company_name, mca_number)
        # Output only JSON (suitable for piping)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        error_result = {
            "source": "zaubacorp.com",
            "company_name": company_name,
            "mca_number": mca_number,
            "error": {
                "type": "NETWORK_ERROR",
                "message": f"Failed to initialize automation: {str(e)}"
            }
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
    finally:
        if agent:
            agent.close()

if __name__ == "__main__":
    main()