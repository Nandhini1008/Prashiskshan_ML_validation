#!/usr/bin/env python3
"""
GST Business Details Automation Agent (Selenium Version)
Fetches publicly available GST information from gstsearch.in
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
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages missing. Install with:")
    print("pip install selenium webdriver-manager beautifulsoup4")
    sys.exit(1)

# Load ChromeDriver path from environment variable (optional)
# If not set, will use system PATH
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "")

class GSTAutomationAgent:
    """Backend automation agent for GST details extraction using Selenium"""
    
    # GSTIN validation regex as per official format
    GSTIN_PATTERN = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    BASE_URL = "https://www.gstsearch.in"
    
    def __init__(self, headless: bool = False):
        """
        Initialize Selenium WebDriver with anti-bot detection
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
                # Use ChromeDriver from system PATH
                self.driver = webdriver.Chrome(options=options)
            
            # Remove webdriver property to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except WebDriverException as e:
            raise Exception(f"Failed to initialize Chrome WebDriver: {str(e)}")
    
    def validate_gstin(self, gstin: str) -> bool:
        """
        Validate GSTIN format using official regex pattern
        Returns: True if valid, False otherwise
        """
        if not gstin or not isinstance(gstin, str):
            return False
        return bool(re.match(self.GSTIN_PATTERN, gstin.strip().upper()))
    
    def normalize_key(self, key: str) -> str:
        """
        Convert field names to snake_case
        Examples: "Legal Name" -> "legal_name", "GSTIN" -> "gstin"
        """
        # Remove extra whitespace and convert to lowercase
        normalized = key.strip().lower()
        # Replace spaces and hyphens with underscores
        normalized = re.sub(r'[\s\-]+', '_', normalized)
        # Remove special characters except underscores
        normalized = re.sub(r'[^\w_]', '', normalized)
        # Remove multiple consecutive underscores
        normalized = re.sub(r'_+', '_', normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        return normalized
    
    def human_like_typing(self, element, text: str, min_delay: float = 0.05, max_delay: float = 0.15):
        """
        Simulate human-like typing with random delays
        Args:
            element: WebElement to type into
            text: Text to type
            min_delay: Minimum delay between keystrokes
            max_delay: Maximum delay between keystrokes
        """
        import random
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))
    
    def fetch_gst_details(self, gstin: str) -> Dict[str, Any]:
        """
        Main automation logic to fetch GST details using Selenium
        Returns: Structured JSON response
        """
        gstin = gstin.strip().upper()
        
        # Step 1: Validate GSTIN format
        if not self.validate_gstin(gstin):
            return {
                "source": "gstsearch.in",
                "gstin": gstin,
                "error": {
                    "type": "INVALID_GSTIN",
                    "message": f"Invalid GSTIN format. Expected pattern: {self.GSTIN_PATTERN}"
                }
            }
        
        try:
            # Step 2: Navigate to website
            try:
                self.driver.get(self.BASE_URL)
                wait = WebDriverWait(self.driver, 20)
            except WebDriverException as e:
                return {
                    "source": "gstsearch.in",
                    "gstin": gstin,
                    "error": {
                        "type": "NETWORK_ERROR",
                        "message": f"Failed to load website: {str(e)}"
                    }
                }
            
            # Step 3: Locate input field and submit form
            try:
                # Wait for input field to be present
                input_box = wait.until(
                    EC.presence_of_element_located((By.ID, "gst"))
                )
                
                # Clear any existing value
                input_box.clear()
                time.sleep(0.5)
                
                # Human-like typing
                self.human_like_typing(input_box, gstin)
                
                # Small delay before pressing Enter
                time.sleep(0.5)
                
                # Submit the form
                input_box.send_keys(Keys.ENTER)
                
            except (TimeoutException, NoSuchElementException) as e:
                return {
                    "source": "gstsearch.in",
                    "gstin": gstin,
                    "error": {
                        "type": "PARSE_ERROR",
                        "message": f"Input field not found: {str(e)}"
                    }
                }
            
            # Step 4: Wait for results table to load
            try:
                wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                # Additional wait for full render
                time.sleep(2)
                
            except TimeoutException:
                # Check if "no record found" message appears
                page_text = self.driver.page_source.lower()
                if any(phrase in page_text for phrase in ['no record found', 'not found', 'invalid']):
                    return {
                        "source": "gstsearch.in",
                        "gstin": gstin,
                        "error": {
                            "type": "NOT_FOUND",
                            "message": "No GST record found for the provided GSTIN"
                        }
                    }
                
                return {
                    "source": "gstsearch.in",
                    "gstin": gstin,
                    "error": {
                        "type": "PARSE_ERROR",
                        "message": "Results table did not load within timeout period"
                    }
                }
            
            # Step 5: Parse HTML response
            html = self.driver.page_source
            return self.parse_response(html, gstin)
            
        except Exception as e:
            return {
                "source": "gstsearch.in",
                "gstin": gstin,
                "error": {
                    "type": "PARSE_ERROR",
                    "message": f"Unexpected error: {str(e)}"
                }
            }
    
    def parse_response(self, html: str, gstin: str) -> Dict[str, Any]:
        """
        Parse HTML response and extract GST details from table
        Returns: Structured JSON response
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for "no record found" or similar messages
        page_text = soup.get_text().lower()
        if any(phrase in page_text for phrase in ['no record found', 'not found', 'invalid gstin']):
            return {
                "source": "gstsearch.in",
                "gstin": gstin,
                "error": {
                    "type": "NOT_FOUND",
                    "message": "No GST record found for the provided GSTIN"
                }
            }
        
        # Locate the results table
        table = soup.find('table')
        
        if not table:
            return {
                "source": "gstsearch.in",
                "gstin": gstin,
                "error": {
                    "type": "PARSE_ERROR",
                    "message": "Results table not found in response"
                }
            }
        
        # Extract data from table rows
        raw_data = {}
        rows = table.find_all('tr')
        
        for row in rows:
            # Find all th and td elements
            cols = row.find_all(['th', 'td'])
            
            # Process pairs of columns (key-value)
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                
                if key and value:
                    normalized_key = self.normalize_key(key)
                    raw_data[normalized_key] = value
        
        if not raw_data:
            return {
                "source": "gstsearch.in",
                "gstin": gstin,
                "error": {
                    "type": "PARSE_ERROR",
                    "message": "No data extracted from table"
                }
            }
        
        # Return successful response with extracted data
        return {
            "source": "gstsearch.in",
            "gstin": gstin,
            "data": raw_data
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
    Usage: python script.py <GSTIN> [--headless]
    """
    if len(sys.argv) < 2:
        print("Usage: python script.py <GSTIN> [--headless]", file=sys.stderr)
        print("Example: python script.py 27AAACR4849R2ZK", file=sys.stderr)
        print("Example: python script.py 27AAACR4849R2ZK --headless", file=sys.stderr)
        sys.exit(1)
    
    gstin = sys.argv[1]
    headless = '--headless' in sys.argv
    
    agent = None
    try:
        agent = GSTAutomationAgent(headless=headless)
        result = agent.fetch_gst_details(gstin)
        # Output only JSON (suitable for piping)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        error_result = {
            "source": "gstsearch.in",
            "gstin": gstin,
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