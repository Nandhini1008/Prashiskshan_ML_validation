"""
LinkedIn & Web Research Agent for Company Employability & Intern Experience Validation

This agent uses Tavily API for web searching to assess:
1. Employability Strength (employee count, hiring signals, activity)
2. Intern Experience Feedback (reviews, sentiment, themes)

CONSTRAINTS:
- No LinkedIn login required
- Uses only public search results and snippets
- Multiple independent sources for validation
- No hallucination - explicit when data unavailable
"""

import json
import os
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter

from tavily import TavilyClient
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - Load from environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


class CompanyResearchAgent:
    """Agent to research company employability and intern experience"""
    
    def __init__(self):
        """Initialize the research agent with Tavily"""
        self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        self.results = {
            "company": "",
            "employability_strength": "UNKNOWN",
            "employee_strength_estimate": "Unknown",
            "hiring_activity_signal": "UNKNOWN",
            "intern_feedback_summary": {
                "overall_sentiment": "INSUFFICIENT_DATA",
                "common_themes": [],
                "sources_found": []
            },
            "recent_activity_evidence": "",
            "confidence_level": "LOW",
            "notes": ""
        }
        
    def tavily_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Perform web search using Tavily API and extract results
        
        Args:
            query: Search query
            num_results: Number of results to extract
            
        Returns:
            List of dicts with title, url, snippet
        """
        print(f"  🔎 Searching: {query}")
        
        try:
            response = self.tavily_client.search(
                query=query,
                max_results=num_results,
                include_raw_content=False
            )
            
            results = []
            for item in response.get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('content', '')
                })
            
            print(f"    ✅ Found {len(results)} results")
            return results
            
        except Exception as e:
            print(f"    ❌ Search error: {e}")
            return []
    
    def extract_employee_count(self, text: str) -> Optional[str]:
        """Extract employee count from text snippets"""
        patterns = [
            # LinkedIn format: "10,001+ employees" or "1,001-5,000 employees"
            r'([\d,]+\+?)\s*employees',
            r'([\d,]+-[\d,]+)\s*employees',
            # Range format: "50-200 employees"
            r'(\d+\s*-\s*\d+)\s*employees',
            # Simple format: "500+ employees"
            r'(\d+\+)\s*employees',
            # Team of X
            r'team\s+of\s+([\d,]+)',
            # X people
            r'([\d,]+)\s*people',
            # Employee size categories
            r'(11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10000\+)\s*employees'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count_str = match.group(1)
                # Skip if it's just "001" or similar leading zeros
                if count_str.replace(',', '').replace('+', '').replace('-', '').lstrip('0') == '':
                    continue
                # Clean up the format
                if '-' in count_str:
                    return f"{count_str} employees"
                elif '+' in count_str:
                    return f"{count_str} employees"
                else:
                    return f"{count_str}+ employees"
        return None
    
    def extract_hiring_signals(self, text: str) -> List[str]:
        """Extract hiring-related keywords from text"""
        hiring_keywords = [
            'hiring', 'recruiting', 'join our team', 'we are growing',
            'careers', 'job openings', 'now hiring', 'expanding team',
            'looking for', 'opportunities', 'apply now'
        ]
        
        found_signals = []
        text_lower = text.lower()
        
        for keyword in hiring_keywords:
            if keyword in text_lower:
                found_signals.append(keyword)
        
        return found_signals
    
    def extract_date_signals(self, text: str) -> Optional[str]:
        """Extract recent activity dates from text"""
        # Look for relative dates
        relative_patterns = [
            r'(\d+)\s*(day|week|month)s?\s*ago',
            r'(yesterday|today)',
            r'(last|this)\s+(week|month)'
        ]
        
        for pattern in relative_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Look for absolute dates (2024, Dec 2024, etc.)
        date_patterns = [
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
            r'\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def analyze_intern_sentiment(self, text: str) -> str:
        """Analyze sentiment of intern feedback"""
        positive_keywords = [
            'great', 'excellent', 'amazing', 'wonderful', 'good', 'best',
            'learned', 'growth', 'supportive', 'helpful', 'recommend',
            'opportunity', 'valuable', 'rewarding', 'fantastic', 'love'
        ]
        
        negative_keywords = [
            'bad', 'terrible', 'awful', 'worst', 'poor', 'disappointing',
            'unpaid', 'no pay', 'scam', 'fake', 'waste', 'avoid',
            'not recommend', 'regret', 'horrible', 'toxic', 'exploitative'
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        if positive_count > negative_count * 2:
            return "POSITIVE"
        elif negative_count > positive_count * 2:
            return "NEGATIVE"
        elif positive_count > 0 or negative_count > 0:
            return "NEUTRAL"
        else:
            return "INSUFFICIENT_DATA"
    
    def extract_intern_themes(self, texts: List[str]) -> List[str]:
        """Extract common themes from intern feedback"""
        theme_keywords = {
            'learning opportunities': ['learn', 'learning', 'training', 'skill', 'knowledge'],
            'mentorship quality': ['mentor', 'guidance', 'support', 'supervisor', 'manager'],
            'stipend/compensation': ['stipend', 'pay', 'paid', 'salary', 'compensation', 'unpaid'],
            'work culture': ['culture', 'environment', 'team', 'colleagues', 'workplace'],
            'conversion to full-time': ['conversion', 'full-time', 'ppo', 'offer', 'hired'],
            'work-life balance': ['work-life', 'balance', 'hours', 'workload', 'overtime'],
            'real projects': ['project', 'real work', 'hands-on', 'practical', 'experience'],
            'career growth': ['growth', 'career', 'development', 'advancement', 'opportunity']
        }
        
        theme_counts = Counter()
        combined_text = ' '.join(texts).lower()
        
        for theme, keywords in theme_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    theme_counts[theme] += 1
        
        # Return top themes
        return [theme for theme, count in theme_counts.most_common(5) if count > 0]
    
    def search_linkedin_company_signals(self, company_name: str) -> Dict:
        """Search for LinkedIn company page signals"""
        print(f"\n📊 Searching LinkedIn Company Signals for: {company_name}")
        
        queries = [
            f'site:linkedin.com/company "{company_name}"',
            f'"{company_name}" employees LinkedIn',
            f'"{company_name}" hiring LinkedIn'
        ]
        
        all_results = []
        employee_counts = []
        hiring_signals = []
        activity_dates = []
        
        for query in queries:
            results = self.tavily_search(query, num_results=5)
            all_results.extend(results)
            time.sleep(1)  # Rate limiting
        
        # Analyze results
        for result in all_results:
            combined_text = f"{result['title']} {result['snippet']}"
            
            # Extract employee count
            emp_count = self.extract_employee_count(combined_text)
            if emp_count:
                employee_counts.append(emp_count)
            
            # Extract hiring signals
            signals = self.extract_hiring_signals(combined_text)
            hiring_signals.extend(signals)
            
            # Extract dates
            date = self.extract_date_signals(combined_text)
            if date:
                activity_dates.append(date)
        
        return {
            'results': all_results,
            'employee_counts': employee_counts,
            'hiring_signals': hiring_signals,
            'activity_dates': activity_dates
        }
    
    def search_intern_feedback(self, company_name: str) -> Dict:
        """Search for intern experience and feedback"""
        print(f"\n💬 Searching Intern Feedback for: {company_name}")
        
        queries = [
            f'"{company_name}" intern LinkedIn',
            f'"{company_name}" internship review',
            f'"{company_name}" intern experience',
            f'"{company_name}" intern review site:glassdoor.com',
            f'"{company_name}" intern review site:ambitionbox.com',
            f'"{company_name}" intern site:reddit.com',
            f'"{company_name}" internship experience blog'
        ]
        
        all_results = []
        feedback_texts = []
        sources = []
        
        for query in queries:
            results = self.tavily_search(query, num_results=5)
            all_results.extend(results)
            time.sleep(1)  # Rate limiting
        
        # Analyze results
        for result in all_results:
            combined_text = f"{result['title']} {result['snippet']}"
            feedback_texts.append(combined_text)
            
            # Track sources
            url = result['url'].lower()
            if 'linkedin' in url:
                sources.append('LinkedIn')
            elif 'glassdoor' in url:
                sources.append('Glassdoor')
            elif 'ambitionbox' in url:
                sources.append('AmbitionBox')
            elif 'reddit' in url:
                sources.append('Reddit')
            else:
                sources.append('Blog/Other')
        
        # Analyze sentiment
        sentiments = [self.analyze_intern_sentiment(text) for text in feedback_texts]
        sentiment_counts = Counter(sentiments)
        
        # Determine overall sentiment
        if sentiment_counts['POSITIVE'] > sentiment_counts['NEGATIVE'] * 2:
            overall_sentiment = 'POSITIVE'
        elif sentiment_counts['NEGATIVE'] > sentiment_counts['POSITIVE'] * 2:
            overall_sentiment = 'NEGATIVE'
        elif sentiment_counts['POSITIVE'] > 0 or sentiment_counts['NEGATIVE'] > 0:
            overall_sentiment = 'NEUTRAL'
        else:
            overall_sentiment = 'INSUFFICIENT_DATA'
        
        # Extract themes
        themes = self.extract_intern_themes(feedback_texts)
        
        return {
            'results': all_results,
            'overall_sentiment': overall_sentiment,
            'themes': themes,
            'sources': list(set(sources)),
            'sentiment_breakdown': dict(sentiment_counts)
        }
    
    def calculate_employability_strength(self, linkedin_data: Dict, intern_data: Dict) -> str:
        """Calculate employability strength based on collected signals"""
        
        # Check for strong signals
        has_employee_data = len(linkedin_data['employee_counts']) > 0
        has_hiring_signals = len(linkedin_data['hiring_signals']) > 3
        has_recent_activity = len(linkedin_data['activity_dates']) > 0
        positive_feedback = intern_data['overall_sentiment'] == 'POSITIVE'
        
        strong_signals = sum([has_employee_data, has_hiring_signals, has_recent_activity, positive_feedback])
        
        if strong_signals >= 3:
            return "STRONG"
        elif strong_signals >= 2:
            return "MODERATE"
        elif strong_signals >= 1:
            return "WEAK"
        else:
            return "UNKNOWN"
    
    def calculate_hiring_activity(self, hiring_signals: List[str], activity_dates: List[str]) -> str:
        """Calculate hiring activity level"""
        
        if len(hiring_signals) >= 5 and len(activity_dates) >= 2:
            return "ACTIVE"
        elif len(hiring_signals) >= 2 or len(activity_dates) >= 1:
            return "OCCASIONAL"
        elif len(hiring_signals) >= 1:
            return "LOW"
        else:
            return "UNKNOWN"
    
    def calculate_confidence(self, linkedin_data: Dict, intern_data: Dict) -> str:
        """Calculate confidence level based on data availability"""
        
        linkedin_results = len(linkedin_data['results'])
        intern_results = len(intern_data['results'])
        has_multiple_sources = len(intern_data['sources']) >= 2
        
        total_signals = (
            len(linkedin_data['employee_counts']) +
            len(linkedin_data['hiring_signals']) +
            len(linkedin_data['activity_dates']) +
            len(intern_data['themes'])
        )
        
        if total_signals >= 10 and has_multiple_sources and linkedin_results >= 5:
            return "HIGH"
        elif total_signals >= 5 and (has_multiple_sources or linkedin_results >= 3):
            return "MEDIUM"
        else:
            return "LOW"
    
    def research_company(self, company_name: str) -> Dict:
        """
        Main research function to assess company employability and intern experience
        
        Args:
            company_name: Name of the company to research
            
        Returns:
            Dict with complete assessment
        """
        print(f"\n{'='*60}")
        print(f"🔍 RESEARCHING COMPANY: {company_name}")
        print(f"{'='*60}")
        
        try:
            # Search LinkedIn company signals
            linkedin_data = self.search_linkedin_company_signals(company_name)
            
            # Search intern feedback
            intern_data = self.search_intern_feedback(company_name)
            
            # Build results
            self.results['company'] = company_name
            
            # Employee strength
            if linkedin_data['employee_counts']:
                self.results['employee_strength_estimate'] = linkedin_data['employee_counts'][0]
            
            # Hiring activity
            self.results['hiring_activity_signal'] = self.calculate_hiring_activity(
                linkedin_data['hiring_signals'],
                linkedin_data['activity_dates']
            )
            
            # Intern feedback
            self.results['intern_feedback_summary'] = {
                'overall_sentiment': intern_data['overall_sentiment'],
                'common_themes': intern_data['themes'],
                'sources_found': intern_data['sources']
            }
            
            # Recent activity
            if linkedin_data['activity_dates']:
                self.results['recent_activity_evidence'] = f"Activity found: {', '.join(linkedin_data['activity_dates'][:3])}"
            else:
                self.results['recent_activity_evidence'] = "No recent activity evidence found"
            
            # Employability strength
            self.results['employability_strength'] = self.calculate_employability_strength(
                linkedin_data, intern_data
            )
            
            # Confidence level
            self.results['confidence_level'] = self.calculate_confidence(
                linkedin_data, intern_data
            )
            
            # Notes
            notes = []
            if linkedin_data['employee_counts']:
                notes.append(f"Employee data found: {', '.join(linkedin_data['employee_counts'][:2])}")
            if linkedin_data['hiring_signals']:
                notes.append(f"Hiring signals detected: {len(linkedin_data['hiring_signals'])} instances")
            if intern_data['sources']:
                notes.append(f"Feedback sources: {', '.join(set(intern_data['sources']))}")
            if intern_data['overall_sentiment'] != 'INSUFFICIENT_DATA':
                notes.append(f"Intern sentiment: {intern_data['overall_sentiment']}")
            
            self.results['notes'] = "; ".join(notes) if notes else "Limited public data available"
            
            print(f"\n{'='*60}")
            print(f"✅ RESEARCH COMPLETE")
            print(f"{'='*60}")
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ Error during research: {e}")
            self.results['notes'] = f"Error occurred: {str(e)}"
            return self.results
    
    def save_results(self, output_dir: str = None):
        """Save results to JSON file"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
        
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{self.results['company'].replace(' ', '_')}_employability_report.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filepath}")
        return filepath
    
    def print_results(self):
        """Print formatted results to console"""
        print(f"\n{'='*60}")
        print(f"EMPLOYABILITY ASSESSMENT: {self.results['company']}")
        print(f"{'='*60}")
        print(f"\n📊 EMPLOYABILITY STRENGTH: {self.results['employability_strength']}")
        print(f"👥 Employee Estimate: {self.results['employee_strength_estimate']}")
        print(f"📈 Hiring Activity: {self.results['hiring_activity_signal']}")
        print(f"🎯 Confidence Level: {self.results['confidence_level']}")
        
        print(f"\n💬 INTERN FEEDBACK SUMMARY:")
        print(f"   Sentiment: {self.results['intern_feedback_summary']['overall_sentiment']}")
        
        if self.results['intern_feedback_summary']['common_themes']:
            print(f"   Common Themes:")
            for theme in self.results['intern_feedback_summary']['common_themes']:
                print(f"      • {theme}")
        
        if self.results['intern_feedback_summary']['sources_found']:
            print(f"   Sources: {', '.join(self.results['intern_feedback_summary']['sources_found'])}")
        
        print(f"\n📅 Recent Activity: {self.results['recent_activity_evidence']}")
        print(f"\n📝 Notes: {self.results['notes']}")
        print(f"\n{'='*60}\n")


def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) > 1:
        company_name = " ".join(sys.argv[1:])
    else:
        company_name = input("Enter company name to research: ")
    
    # Create agent
    agent = CompanyResearchAgent()
    
    # Research company
    results = agent.research_company(company_name)
    
    # Print results
    agent.print_results()
    
    # Save results
    agent.save_results()
    
    return results


if __name__ == "__main__":
    main()
