#!/usr/bin/env python3
"""
Test script for Tavily integration with main validation service
"""

import asyncio
import json
from zaubacorp_tavily import ZaubacorpTavilyScraper

async def test_tavily_scraper():
    """Test the Tavily scraper"""
    print("=" * 80)
    print("Testing Zaubacorp Tavily Scraper Integration")
    print("=" * 80)
    
    # Test data
    company_name = "ZOHO CORPORATION PRIVATE LIMITED"
    cin_number = "U40100TN2010PTC075961"
    
    print(f"\nCompany: {company_name}")
    print(f"CIN: {cin_number}\n")
    
    # Create scraper
    scraper = ZaubacorpTavilyScraper()
    
    # Fetch company details
    result = scraper.fetch_company_details(company_name, cin_number)
    
    # Display results
    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Check if successful
    if result.get("data"):
        print("\n✅ SUCCESS: Company details retrieved")
        print(f"   Company Name: {result['data'].get('Name')}")
        print(f"   Company Status: {result['data'].get('Company Status')}")
        print(f"   CIN: {result['data'].get('CIN')}")
    else:
        print("\n❌ FAILED: Could not retrieve company details")
        if result.get("error"):
            print(f"   Error: {result['error'].get('message')}")

if __name__ == "__main__":
    asyncio.run(test_tavily_scraper())
