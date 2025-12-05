#!/usr/bin/env python3
"""
Company Legitimacy Validation Service

This service takes company name, CIN number, and GST number as inputs,
runs all validations asynchronously (GST, MCA, Reddit, LinkedIn),
and determines if the company is legitimate.

Usage:
    python main.py "<company_name>" <cin_number> <gst_number>
    
Example:
    python main.py "Zoho Corporation" U72900KA2018PTC123456 29AABCT1332L1ZU
"""

import asyncio
import json
import sys
import time
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import validation agents
from gst import GSTAutomationAgent
from mca import MCAAutomationAgent
from zaubacorp_tavily import ZaubacorpTavilyScraper
from reddit import check_company_internship_scams
from linked import CompanyResearchAgent


class CompanyLegitimacyValidator:
    """
    Main validator that orchestrates all validations asynchronously
    and determines company legitimacy
    """
    
    # Validation patterns
    CIN_PATTERN = r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'
    GST_PATTERN = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    def __init__(self, company_name: str, cin_number: str, gst_number: str):
        """
        Initialize the validator
        
        Args:
            company_name: Name of the company
            cin_number: Corporate Identification Number (21 characters)
            gst_number: GST Identification Number (15 characters)
        """
        self.company_name = company_name.strip()
        self.cin_number = cin_number.strip().upper()
        self.gst_number = gst_number.strip().upper()
        
        # Results storage
        self.gst_result = None
        self.mca_result = None
        self.reddit_result = None
        self.linkedin_result = None
        self.validation_start_time = None
        self.validation_end_time = None
        
        # Validation errors
        self.validation_errors = []
    
    def validate_input_format(self) -> bool:
        """
        Validate input formats before processing
        
        Returns:
            bool: True if all inputs are valid, False otherwise
        """
        print("\n" + "=" * 80)
        print("🔍 Validating Input Formats")
        print("=" * 80 + "\n")
        
        is_valid = True
        
        # Validate CIN number length and format
        if len(self.cin_number) != 21:
            error_msg = f"❌ CIN number must be exactly 21 characters (provided: {len(self.cin_number)})"
            print(error_msg)
            self.validation_errors.append(error_msg)
            is_valid = False
        elif not re.match(self.CIN_PATTERN, self.cin_number):
            error_msg = f"❌ CIN number format is invalid: {self.cin_number}"
            print(error_msg)
            self.validation_errors.append(error_msg)
            is_valid = False
        else:
            print(f"✅ CIN number format valid: {self.cin_number} (21 characters)")
        
        # Validate GST number length and format
        if len(self.gst_number) != 15:
            error_msg = f"❌ GST number must be exactly 15 characters (provided: {len(self.gst_number)})"
            print(error_msg)
            self.validation_errors.append(error_msg)
            is_valid = False
        elif not re.match(self.GST_PATTERN, self.gst_number):
            error_msg = f"❌ GST number format is invalid: {self.gst_number}"
            print(error_msg)
            self.validation_errors.append(error_msg)
            is_valid = False
        else:
            print(f"✅ GST number format valid: {self.gst_number} (15 characters)")
        
        # Validate company name
        if not self.company_name or len(self.company_name) < 2:
            error_msg = "❌ Company name is too short or empty"
            print(error_msg)
            self.validation_errors.append(error_msg)
            is_valid = False
        else:
            print(f"✅ Company name valid: {self.company_name}")
        
        print("\n" + "=" * 80 + "\n")
        
        return is_valid
    
    async def validate_gst_async(self) -> Dict[str, Any]:
        """Run GST validation asynchronously in headless mode"""
        print(f"🔍 Starting GST validation for {self.gst_number}...")
        
        try:
            loop = asyncio.get_event_loop()
            
            def run_gst_validation():
                agent = None
                try:
                    # Always run in headless mode
                    agent = GSTAutomationAgent(headless=True)
                    result = agent.fetch_gst_details(self.gst_number)
                    return result
                finally:
                    if agent:
                        agent.close()
            
            result = await loop.run_in_executor(None, run_gst_validation)
            
            if result.get('error'):
                print(f"❌ GST validation failed: {result['error']['message']}")
            else:
                print(f"✅ GST validation complete")
            
            return result
            
        except Exception as e:
            print(f"❌ GST validation error: {str(e)}")
            return {
                "source": "gstsearch.in",
                "gstin": self.gst_number,
                "error": {
                    "type": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
    
    async def validate_mca_async(self) -> Dict[str, Any]:
        """Run MCA validation asynchronously using Tavily API scraper"""
        print(f"🔍 Starting MCA validation for {self.company_name} / {self.cin_number}...")
        
        try:
            loop = asyncio.get_event_loop()
            
            def run_mca_validation():
                try:
                    # Use Tavily-based scraper (faster and more reliable)
                    scraper = ZaubacorpTavilyScraper()
                    result = scraper.fetch_company_details(self.company_name, self.cin_number)
                    return result
                except Exception as e:
                    return {
                        "source": "zaubacorp.com",
                        "company_name": self.company_name,
                        "mca_number": self.cin_number,
                        "error": {
                            "type": "VALIDATION_ERROR",
                            "message": str(e)
                        }
                    }
            
            result = await loop.run_in_executor(None, run_mca_validation)
            
            if result.get('error'):
                print(f"❌ MCA validation failed: {result['error']['message']}")
            else:
                print(f"✅ MCA validation complete")
            
            return result
            
        except Exception as e:
            print(f"❌ MCA validation error: {str(e)}")
            return {
                "source": "zaubacorp.com",
                "company_name": self.company_name,
                "mca_number": self.cin_number,
                "error": {
                    "type": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
    
    async def validate_reddit_async(self) -> Dict[str, Any]:
        """Run Reddit scam check asynchronously"""
        print(f"🔍 Starting Reddit scam check for {self.company_name}...")
        
        try:
            loop = asyncio.get_event_loop()
            
            def run_reddit_check():
                try:
                    result = check_company_internship_scams(self.company_name, max_comments=15)
                    return result
                except Exception as e:
                    return {
                        "company_name": self.company_name,
                        "scam_reports_found": False,
                        "error": str(e)
                    }
            
            result = await loop.run_in_executor(None, run_reddit_check)
            
            if result.get('error'):
                print(f"❌ Reddit check failed: {result.get('error')}")
            else:
                print(f"✅ Reddit check complete")
            
            return result
            
        except Exception as e:
            print(f"❌ Reddit check error: {str(e)}")
            return {
                "company_name": self.company_name,
                "scam_reports_found": False,
                "error": str(e)
            }
    
    async def validate_linkedin_async(self) -> Dict[str, Any]:
        """Run LinkedIn/employability check asynchronously"""
        print(f"🔍 Starting LinkedIn/employability check for {self.company_name}...")
        
        try:
            loop = asyncio.get_event_loop()
            
            def run_linkedin_check():
                try:
                    agent = CompanyResearchAgent()
                    result = agent.research_company(self.company_name)
                    return result
                except Exception as e:
                    return {
                        "company": self.company_name,
                        "employability_strength": "UNKNOWN",
                        "error": str(e)
                    }
            
            result = await loop.run_in_executor(None, run_linkedin_check)
            
            if result.get('error'):
                print(f"❌ LinkedIn check failed: {result.get('error')}")
            else:
                print(f"✅ LinkedIn check complete")
            
            return result
            
        except Exception as e:
            print(f"❌ LinkedIn check error: {str(e)}")
            return {
                "company": self.company_name,
                "employability_strength": "UNKNOWN",
                "error": str(e)
            }
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validations concurrently"""
        print("\n" + "=" * 80)
        print("🚀 Starting Company Legitimacy Validation")
        print("=" * 80)
        print(f"Company Name: {self.company_name}")
        print(f"CIN Number: {self.cin_number}")
        print(f"GST Number: {self.gst_number}")
        print("=" * 80 + "\n")
        
        # Validate input formats first
        if not self.validate_input_format():
            return {
                "validation_summary": {
                    "company_name": self.company_name,
                    "cin_number": self.cin_number,
                    "gst_number": self.gst_number,
                    "validation_timestamp": datetime.now().isoformat(),
                    "status": "FAILED"
                },
                "legitimacy_assessment": {
                    "status": "❌ VALIDATION FAILED",
                    "classification": "INVALID_INPUT",
                    "errors": self.validation_errors
                }
            }
        
        self.validation_start_time = time.time()
        
        # Run all validations concurrently
        print("⚡ Running all validations in parallel...\n")
        
        gst_task = asyncio.create_task(self.validate_gst_async())
        mca_task = asyncio.create_task(self.validate_mca_async())
        reddit_task = asyncio.create_task(self.validate_reddit_async())
        linkedin_task = asyncio.create_task(self.validate_linkedin_async())
        
        # Wait for all to complete
        self.gst_result, self.mca_result, self.reddit_result, self.linkedin_result = await asyncio.gather(
            gst_task, mca_task, reddit_task, linkedin_task
        )
        
        self.validation_end_time = time.time()
        
        # Analyze results and determine legitimacy
        legitimacy_result = self.analyze_legitimacy()
        
        return legitimacy_result
    
    def check_cin_consistency(self) -> bool:
        """Check if CIN from input matches CIN from MCA scraping"""
        if not self.mca_result or self.mca_result.get('error'):
            return False
        
        mca_data = self.mca_result.get('data', {})
        scraped_cin = mca_data.get('CIN', '').strip().upper()
        
        if scraped_cin and scraped_cin == self.cin_number:
            return True
        
        return False
    
    def analyze_legitimacy(self) -> Dict[str, Any]:
        """
        Analyze validation results and determine if company is legitimate
        
        Returns:
            Dictionary with legitimacy assessment
        """
        print("\n" + "=" * 80)
        print("📊 Analyzing Results")
        print("=" * 80 + "\n")
        
        # Initialize scores
        gst_score = 0
        mca_score = 0
        consistency_score = 0
        reddit_score = 0
        linkedin_score = 0
        total_score = 0
        
        red_flags = []
        green_flags = []
        
        # Analyze GST validation (30 points max)
        if self.gst_result and not self.gst_result.get('error'):
            gst_score = 20  # GST validation successful
            green_flags.append("GST number is valid and registered")
            
            gst_data = self.gst_result.get('data', {})
            if gst_data.get('Status', '').lower() == 'active':
                gst_score += 10
                green_flags.append("GST status is Active")
            else:
                red_flags.append(f"GST status is {gst_data.get('Status', 'Unknown')}")
        else:
            red_flags.append("GST validation failed or number not found")
        
        # Analyze MCA validation (30 points max)
        if self.mca_result and not self.mca_result.get('error'):
            mca_score = 20  # MCA validation successful
            green_flags.append("CIN number is valid and company is registered")
            
            mca_data = self.mca_result.get('data', {})
            company_status = mca_data.get('Company Status', '').lower()
            
            if 'active' in company_status:
                mca_score += 10
                green_flags.append("Company status is Active")
            else:
                red_flags.append(f"Company status is {mca_data.get('Company Status', 'Unknown')}")
        else:
            red_flags.append("MCA validation failed or CIN not found")
        
        # Check CIN consistency (10 points)
        if self.check_cin_consistency():
            consistency_score = 10
            green_flags.append("CIN number matches between input and MCA records")
        else:
            red_flags.append("CIN number mismatch or not verifiable")
        
        # Analyze Reddit scam reports (20 points max)
        if self.reddit_result and not self.reddit_result.get('error'):
            if self.reddit_result.get('classification') == 'LEGIT':
                reddit_score = 20
                green_flags.append("No scam reports found on Reddit")
            elif self.reddit_result.get('classification') == 'SCAM':
                reddit_score = 0
                red_flags.append(f"Scam reports found on Reddit ({self.reddit_result.get('scam_comment_count', 0)} reports)")
            else:
                reddit_score = 10
                green_flags.append("Limited Reddit data available")
        else:
            reddit_score = 10  # Neutral if no data
        
        # Analyze LinkedIn/employability (10 points max)
        if self.linkedin_result and not self.linkedin_result.get('error'):
            strength = self.linkedin_result.get('employability_strength', 'UNKNOWN')
            if strength == 'STRONG':
                linkedin_score = 10
                green_flags.append("Strong employability signals found")
            elif strength == 'MODERATE':
                linkedin_score = 7
                green_flags.append("Moderate employability signals found")
            elif strength == 'WEAK':
                linkedin_score = 4
                green_flags.append("Weak employability signals found")
            else:
                linkedin_score = 5  # Neutral
        else:
            linkedin_score = 5  # Neutral if no data
        
        # Calculate total score
        total_score = gst_score + mca_score + consistency_score + reddit_score + linkedin_score
        
        # Determine legitimacy classification
        if total_score >= 80:
            classification = "LEGITIMATE"
            confidence = "HIGH"
            legitimacy_status = "✅ COMPANY IS LEGITIMATE"
        elif total_score >= 60:
            classification = "LIKELY LEGITIMATE"
            confidence = "MEDIUM"
            legitimacy_status = "⚠️ COMPANY IS LIKELY LEGITIMATE (Some concerns)"
        elif total_score >= 40:
            classification = "QUESTIONABLE"
            confidence = "LOW"
            legitimacy_status = "⚠️ COMPANY LEGITIMACY IS QUESTIONABLE"
        else:
            classification = "NOT LEGITIMATE"
            confidence = "HIGH"
            legitimacy_status = "❌ COMPANY IS NOT LEGITIMATE"
        
        # Build result
        result = {
            "validation_summary": {
                "company_name": self.company_name,
                "cin_number": self.cin_number,
                "gst_number": self.gst_number,
                "validation_timestamp": datetime.now().isoformat(),
                "validation_duration_seconds": round(self.validation_end_time - self.validation_start_time, 2)
            },
            "legitimacy_assessment": {
                "status": legitimacy_status,
                "classification": classification,
                "confidence_level": confidence,
                "total_score": total_score,
                "max_score": 100,
                "score_breakdown": {
                    "gst_validation_score": gst_score,
                    "mca_validation_score": mca_score,
                    "cin_consistency_score": consistency_score,
                    "reddit_reputation_score": reddit_score,
                    "linkedin_employability_score": linkedin_score
                }
            },
            "flags": {
                "green_flags": green_flags,
                "red_flags": red_flags
            },
            "detailed_results": {
                "gst_validation": self.gst_result,
                "mca_validation": self.mca_result,
                "reddit_scam_check": self.reddit_result,
                "linkedin_employability": self.linkedin_result
            }
        }
        
        # Print summary
        print(f"Status: {legitimacy_status}")
        print(f"Classification: {classification}")
        print(f"Confidence: {confidence}")
        print(f"Total Score: {total_score}/100")
        print(f"\nScore Breakdown:")
        print(f"  - GST Validation: {gst_score}/30")
        print(f"  - MCA Validation: {mca_score}/30")
        print(f"  - CIN Consistency: {consistency_score}/10")
        print(f"  - Reddit Reputation: {reddit_score}/20")
        print(f"  - LinkedIn Employability: {linkedin_score}/10")
        
        if green_flags:
            print(f"\n✅ Green Flags ({len(green_flags)}):")
            for flag in green_flags:
                print(f"  • {flag}")
        
        if red_flags:
            print(f"\n🚩 Red Flags ({len(red_flags)}):")
            for flag in red_flags:
                print(f"  • {flag}")
        
        print("\n" + "=" * 80)
        
        return result
    
    def save_results(self, result: Dict[str, Any], output_file: str = None):
        """Save validation results to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_company_name = "".join(c for c in self.company_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_company_name = safe_company_name.replace(' ', '_')
            output_file = f"{safe_company_name}_{timestamp}_validation.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {str(e)}")


async def main():
    """Main entry point"""
    if len(sys.argv) < 4:
        print("Usage: python main.py \"<company_name>\" <cin_number> <gst_number>")
        print("\nExample:")
        print('  python main.py "Zoho Corporation" U72900KA2018PTC123456 29AABCT1332L1ZU')
        print("\nNote:")
        print("  - Company name should be in quotes if it contains spaces")
        print("  - CIN number must be exactly 21 characters")
        print("  - GST number must be exactly 15 characters")
        print("  - GST and MCA validations run in headless mode by default")
        sys.exit(1)
    
    company_name = sys.argv[1]
    cin_number = sys.argv[2]
    gst_number = sys.argv[3]
    
    # Create validator
    validator = CompanyLegitimacyValidator(
        company_name=company_name,
        cin_number=cin_number,
        gst_number=gst_number
    )
    
    # Run validations
    result = await validator.run_all_validations()
    
    # Save results
    validator.save_results(result)
    
    # Output JSON for programmatic use
    print("\n" + "=" * 80)
    print("📄 JSON Output")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
