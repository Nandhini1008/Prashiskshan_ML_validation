#!/usr/bin/env python3
"""
Test script for Company Validation API
"""

import requests
import json
import sys

# API base URL (change this to your deployed URL)
BASE_URL = "http://localhost:8003"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*80)
    print("Testing Health Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validate_company():
    """Test company validation endpoint"""
    print("\n" + "="*80)
    print("Testing Company Validation Endpoint")
    print("="*80)
    
    # Test data
    payload = {
        "company_name": "ZOHO CORPORATION PRIVATE LIMITED",
        "cin_number": "U40100TN2010PTC075961",
        "gst_number": "33AABCT1332L1ZU"
    }
    
    print(f"\nRequest Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        print(f"\n⏳ Sending request to {BASE_URL}/validate-company...")
        print("   (This may take 10-15 seconds...)")
        
        response = requests.post(
            f"{BASE_URL}/validate-company",
            json=payload,
            timeout=60
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📊 Validation Result:")
            print(f"   Success: {result.get('success')}")
            
            if result.get('legitimacy_assessment'):
                assessment = result['legitimacy_assessment']
                print(f"   Status: {assessment.get('status')}")
                print(f"   Classification: {assessment.get('classification')}")
                print(f"   Confidence: {assessment.get('confidence_level')}")
                print(f"   Total Score: {assessment.get('total_score')}/100")
            
            print(f"\n📄 Full Response:")
            print(json.dumps(result, indent=2))
            
            return True
        else:
            print(f"❌ Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out (>60 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_info():
    """Test API info endpoint"""
    print("\n" + "="*80)
    print("Testing API Info Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api-info")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            info = response.json()
            print(f"\nAPI Name: {info.get('api_name')}")
            print(f"Version: {info.get('version')}")
            print(f"Description: {info.get('description')}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    if len(sys.argv) > 1:
        global BASE_URL
        BASE_URL = sys.argv[1]
    
    print(f"\n{'='*80}")
    print(f"🧪 Company Validation API Test Suite")
    print(f"{'='*80}")
    print(f"Base URL: {BASE_URL}")
    print(f"{'='*80}")
    
    results = {
        "Health Check": test_health(),
        "API Info": test_api_info(),
        "Company Validation": test_validate_company()
    }
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 Test Summary")
    print(f"{'='*80}")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"{'='*80}\n")
    
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
