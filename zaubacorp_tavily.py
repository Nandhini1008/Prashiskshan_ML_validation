#!/usr/bin/env python3
"""
Zaubacorp Company Details Scraper using Tavily API
Searches zaubacorp.com for company information using company name and CIN number
Uses Tavily API for search and ScraperAPI for content extraction

Environment Variables Required:
- TAVILY_API_KEY: Your Tavily API key
- SCRAPER_API_KEY: Your ScraperAPI key (optional, for enhanced scraping)
"""

import os
import sys
import json
import re
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
SCRAPER_API_URL = os.getenv("SCRAPER_API_URL", "http://api.scraperapi.com")

if not TAVILY_API_KEY:
    print("ERROR: TAVILY_API_KEY not found in environment variables", file=sys.stderr)
    sys.exit(1)


class ZaubacorpTavilyScraper:
    """Scraper for Zaubacorp company details using Tavily API"""
    
    TAVILY_API_URL = "https://api.tavily.com/search"
    CIN_PATTERN = r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'
    
    def __init__(self):
        """Initialize the scraper with API keys"""
        self.tavily_api_key = TAVILY_API_KEY
        self.scraper_api_key = SCRAPER_API_KEY
    
    def validate_cin(self, cin: str) -> bool:
        """Validate CIN format"""
        if not cin or not isinstance(cin, str):
            return False
        return bool(re.match(self.CIN_PATTERN, cin.strip().upper()))
    
    def search_zaubacorp(self, company_name: str, cin_number: str) -> Dict[str, Any]:
        """
        Search Zaubacorp using Tavily API
        
        Args:
            company_name: Name of the company
            cin_number: CIN number of the company
            
        Returns:
            Dictionary with search results and company URL
        """
        # Construct search query - search for CIN number specifically
        search_query = f"site:zaubacorp.com {cin_number}"
        
        print(f"🔍 Searching Zaubacorp for: {company_name} ({cin_number})")
        print(f"   Query: {search_query}")
        
        try:
            # Make Tavily API request
            payload = {
                "api_key": self.tavily_api_key,
                "query": search_query,
                "search_depth": "basic",
                "include_answer": False,
                "include_raw_content": False,
                "max_results": 10,
                "include_domains": ["zaubacorp.com"]
            }
            
            response = requests.post(
                self.TAVILY_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": {
                        "type": "API_ERROR",
                        "message": f"Tavily API returned status {response.status_code}: {response.text}"
                    }
                }
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return {
                    "success": False,
                    "error": {
                        "type": "NOT_FOUND",
                        "message": f"No Zaubacorp results found for {company_name} ({cin_number})"
                    }
                }
            
            # Find the company page URL (not address page)
            # Company pages have format: /COMPANY-NAME-CIN or contain the CIN in URL
            company_url = None
            for result in results:
                url = result.get("url", "")
                # Look for URLs that contain the CIN and are company pages
                if cin_number in url and "/company/" not in url and "/company-by-address/" not in url:
                    company_url = url
                    break
                # Also check if URL ends with CIN
                if url.endswith(cin_number):
                    company_url = url
                    break
            
            # If no specific company page found, use first result
            if not company_url:
                company_url = results[0].get("url", "")
            
            print(f"✅ Found company URL: {company_url}")
            
            return {
                "success": True,
                "company_url": company_url,
                "title": results[0].get("title", ""),
                "content_snippet": results[0].get("content", ""),
                "all_results": results
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": {
                    "type": "TIMEOUT",
                    "message": "Tavily API request timed out"
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": {
                    "type": "NETWORK_ERROR",
                    "message": f"Network error: {str(e)}"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "type": "UNKNOWN_ERROR",
                    "message": f"Unexpected error: {str(e)}"
                }
            }
    
    def scrape_company_page(self, url: str) -> Dict[str, Any]:
        """
        Scrape company details from Zaubacorp page
        
        Args:
            url: URL of the company page on Zaubacorp
            
        Returns:
            Dictionary with scraped company details
        """
        print(f"📄 Scraping company page: {url}")
        
        try:
            # Use ScraperAPI if available, otherwise direct request
            if self.scraper_api_key:
                # Use ScraperAPI for better reliability
                scraper_url = f"{SCRAPER_API_URL}?api_key={self.scraper_api_key}&url={url}"
                response = requests.get(scraper_url, timeout=60)
            else:
                # Direct request with headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                }
                response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": {
                        "type": "HTTP_ERROR",
                        "message": f"Failed to fetch page: HTTP {response.status_code}"
                    }
                }
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract company information from table
            company_info = self._parse_company_table(soup)
            
            if not company_info:
                return {
                    "success": False,
                    "error": {
                        "type": "PARSE_ERROR",
                        "message": "Could not extract company information from page"
                    }
                }
            
            print(f"✅ Successfully scraped company details")
            
            return {
                "success": True,
                "data": company_info,
                "source_url": url
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": {
                    "type": "TIMEOUT",
                    "message": "Request timed out while scraping page"
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": {
                    "type": "NETWORK_ERROR",
                    "message": f"Network error: {str(e)}"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "type": "PARSE_ERROR",
                    "message": f"Error parsing page: {str(e)}"
                }
            }
    
    def _parse_company_table(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Parse company information table from Zaubacorp page
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary with company details or None if not found
        """
        # Find the company information table
        table = soup.find('table', class_='table table-striped')
        
        if not table:
            # Try finding any table with company info
            table = soup.find('table', class_='table')
        
        if not table:
            return None
        
        company_info = {}
        tbody = table.find('tbody')
        
        if not tbody:
            # Some tables might not have tbody, try direct tr
            rows = table.find_all('tr')
        else:
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
                            nic_code = text.replace('NIC Code:', '').strip()
                            nic_info['NIC Code'] = nic_code
                        elif 'NIC Description:' in text:
                            nic_desc = text.replace('NIC Description:', '').strip()
                            nic_info['NIC Description'] = nic_desc
                    
                    if nic_info:
                        company_info[key] = nic_info
                    else:
                        # Fallback to full text
                        value = value_cell.get_text(strip=True, separator=' ')
                        company_info[key] = value
                else:
                    # Regular field - extract text, handling links
                    # First try to get just text (ignoring links)
                    value = value_cell.get_text(strip=True)
                    # Clean up extra whitespace
                    value = ' '.join(value.split())
                    company_info[key] = value
        
        return company_info if company_info else None
    
    def fetch_company_details(self, company_name: str, cin_number: str) -> Dict[str, Any]:
        """
        Main method to fetch company details from Zaubacorp
        
        Args:
            company_name: Name of the company
            cin_number: CIN number of the company
            
        Returns:
            Dictionary with complete company information
        """
        company_name = company_name.strip()
        cin_number = cin_number.strip().upper()
        
        # Validate CIN format (warning only)
        if not self.validate_cin(cin_number):
            print(f"⚠️  Warning: CIN number '{cin_number}' may not be in standard format", file=sys.stderr)
        
        # Step 1: Search for company on Zaubacorp
        search_result = self.search_zaubacorp(company_name, cin_number)
        
        if not search_result.get("success"):
            return {
                "source": "zaubacorp.com (via Tavily API)",
                "company_name": company_name,
                "cin_number": cin_number,
                "error": search_result.get("error")
            }
        
        company_url = search_result.get("company_url")
        
        # Step 2: Scrape company details from the page
        scrape_result = self.scrape_company_page(company_url)
        
        if not scrape_result.get("success"):
            return {
                "source": "zaubacorp.com (via Tavily API)",
                "company_name": company_name,
                "cin_number": cin_number,
                "company_url": company_url,
                "error": scrape_result.get("error")
            }
        
        # Return complete result
        return {
            "source": "zaubacorp.com (via Tavily API)",
            "company_name": company_name,
            "cin_number": cin_number,
            "company_url": company_url,
            "data": scrape_result.get("data"),
            "search_metadata": {
                "title": search_result.get("title"),
                "content_snippet": search_result.get("content_snippet")
            }
        }


def main():
    """
    Command-line interface for the Zaubacorp Tavily scraper
    Usage: python zaubacorp_tavily.py "<company_name>" <cin_number>
    """
    if len(sys.argv) < 3:
        print("Usage: python zaubacorp_tavily.py \"<company_name>\" <cin_number>", file=sys.stderr)
        print("Example: python zaubacorp_tavily.py \"Zoho Corporation\" U72900KA2018PTC123456", file=sys.stderr)
        print("\nNote: Company name should be in quotes if it contains spaces", file=sys.stderr)
        sys.exit(1)
    
    company_name = sys.argv[1]
    cin_number = sys.argv[2]
    
    scraper = ZaubacorpTavilyScraper()
    result = scraper.fetch_company_details(company_name, cin_number)
    
    # Output JSON
    print("\n" + "=" * 80)
    print("📊 RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
