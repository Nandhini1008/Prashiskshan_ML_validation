"""
Reddit Internship Scam Detection Agent
Searches Reddit for reports of fake/scam internships from a given company
and summarizes findings using Gemini LLM
Uses ScraperAPI for reliable scraping
"""

from tavily import TavilyClient
import requests
from bs4 import BeautifulSoup
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - Load from environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
SCRAPER_API_URL = os.getenv("SCRAPER_API_URL", "http://api.scraperapi.com")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def tavily_search(query, api_key, company_name, num_results=15):
    """Search for Reddit posts using Tavily API and filter by company name"""
    client = TavilyClient(api_key)
    response = client.search(query=query, max_results=num_results)
    
    # Filter URLs that contain the company name (case-insensitive)
    company_name_lower = company_name.lower()
    reddit_urls = []
    
    for item in response.get('results', []):
        url = item['url']
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        
        # Only include if it's a Reddit URL and mentions the company name
        if 'reddit.com/r/' in url:
            # Check if company name is in URL, title, or content
            if (company_name_lower in url.lower() or 
                company_name_lower in title or 
                company_name_lower in content):
                reddit_urls.append(url)
    
    return reddit_urls


def extract_comment_data(comment_elem, post_url):
    """Extract comment author, text, and URL from a Reddit comment element"""
    author = 'Anonymous'
    comment_text = ''
    comment_url = post_url
    
    # Extract author
    author_link = comment_elem.find('a', href=lambda x: x and '/user/' in x)
    if author_link:
        author = author_link.get_text(strip=True)
    
    # Extract comment text from <p> tags
    text_p = comment_elem.find_all('p')
    if text_p:
        comment_text = "\n".join([p.get_text(strip=True) for p in text_p if p.get_text(strip=True)])
    
    # Try to get comment ID for URL
    thing_id = comment_elem.get('thingid')
    if thing_id and thing_id.startswith('t1_'):
        comment_url = post_url.rstrip('/') + '/comment/' + thing_id[3:]
    
    return {
        'url': comment_url,
        'author': author,
        'comment': comment_text
    }


def is_internship_related(comment_text):
    """Check if a comment is related to internships"""
    internship_keywords = [
        'intern', 'internship', 'trainee', 'training program', 'summer program',
        'stipend', 'apprentice', 'apprenticeship', 'placement', 'campus',
        'fresher', 'graduate program', 'entry level', 'student program',
        'co-op', 'work experience', 'industrial training', 'practical training'
    ]
    
    comment_lower = comment_text.lower()
    return any(keyword in comment_lower for keyword in internship_keywords)


def mentions_company(text, company_name):
    """Check if text mentions the company name"""
    if not text or not company_name:
        return False
    
    text_lower = text.lower()
    company_lower = company_name.lower()
    
    # Check for exact match or partial match (for multi-word company names)
    if company_lower in text_lower:
        return True
    
    # Check for individual words in multi-word company names
    # e.g., "Infosys Springboard" -> check for "infosys" or "springboard"
    company_words = company_lower.split()
    if len(company_words) > 1:
        # At least one significant word should be present
        significant_words = [w for w in company_words if len(w) > 3]  # Skip short words like "the", "and"
        if significant_words and any(word in text_lower for word in significant_words):
            return True
    
    return False


def scrape_reddit_post(url):
    """
    Scrape a Reddit post and extract all comments using ScraperAPI
    
    Args:
        url: Reddit URL to scrape
        
    Returns:
        list: List of comment dictionaries
    """
    print(f"🕸️ Scraping: {url}")
    
    try:
        # ScraperAPI parameters
        params = {
            'api_key': SCRAPER_API_KEY,
            'url': url,
            'render': 'true',  # Enable JavaScript rendering
            'country_code': 'us'
        }
        
        response = requests.get(SCRAPER_API_URL, params=params, timeout=60)
        
        if response.status_code != 200:
            print(f"   ❌ Error: HTTP {response.status_code}")
            return []
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = []
        
        # Method 1: Extract from shreddit-comment elements
        shreddit_comments = soup.find_all('shreddit-comment')
        for comment_elem in shreddit_comments:
            comment_data = extract_comment_data(comment_elem, url)
            if comment_data['comment']:
                comments.append(comment_data)
        
        # Method 2: Extract post content
        post_divs = soup.find_all('div', id=lambda x: x and 'post-rtjson-content' in x)
        for post_div in post_divs:
            text_p = post_div.find_all('p')
            if text_p:
                text = "\n".join([p.get_text(strip=True) for p in text_p if p.get_text(strip=True)])
                if text:
                    comments.insert(0, {
                        'url': url,
                        'author': 'OP',
                        'comment': text
                    })
        
        # Method 3: Extract from scalable-text divs
        scalable_divs = soup.find_all('div', class_=lambda x: x and 'scalable-text' in x)
        for div in scalable_divs:
            text_p = div.find_all('p')
            if text_p:
                text = "\n".join([p.get_text(strip=True) for p in text_p if p.get_text(strip=True)])
                if text and not any(c['comment'] == text for c in comments):
                    comments.append({
                        'url': url,
                        'author': 'Anonymous',
                        'comment': text
                    })
        
        # Filter for internship-related comments only
        internship_comments = []
        for comment in comments:
            if is_internship_related(comment['comment']):
                internship_comments.append(comment)
        
        # Limit to 15 internship-related comments per URL
        internship_comments = internship_comments[:15]
        
        print(f"   ✅ Extracted {len(internship_comments)} internship-related comments (from {len(comments)} total)")
        return internship_comments
    
    except Exception as e:
        print(f"   ❌ Error scraping post: {str(e)}")
        return []


def scrape_reddit_post_with_company_filter(url, company_name):
    """Scrape Reddit post and filter comments that mention the company"""
    # First scrape all comments
    all_comments = scrape_reddit_post(url)
    
    # Filter comments that mention the company name
    company_comments = []
    for comment in all_comments:
        if mentions_company(comment['comment'], company_name):
            company_comments.append(comment)
    
    print(f"   🏢 Filtered to {len(company_comments)} comments mentioning '{company_name}' (from {len(all_comments)} internship-related)")
    return company_comments


def filter_scam_related_comments(comments, company_name):
    """Filter comments that mention scam, fake, fraud, money, or payment issues AND are internship-related"""
    scam_keywords = [
        'scam', 'fake', 'fraud', 'cheat', 'money', 'payment', 'paid', 'fee', 
        'deposit', 'refund', 'unpaid', 'not paid', 'didnt pay', "didn't pay",
        'never paid', 'no payment', 'no salary', 'no stipend', 'beware', 'warning',
        'avoid', 'reported', 'complaint', 'stolen', 'theft', 'illegal', 'support', 'awful'
    ]
    
    filtered = []
    for comment in comments:
        comment_lower = comment['comment'].lower()
        
        # First check if it's internship-related
        if not is_internship_related(comment['comment']):
            continue
        
        # Then check if it has scam-related keywords
        if any(keyword in comment_lower for keyword in scam_keywords):
            filtered.append(comment)
    
    return filtered


def summarize_with_gemini(comments, company_name):
    """Use Gemini LLM to analyze and summarize scam reports into bullet points"""
    if not comments:
        return {
            "company_name": company_name,
            "scam_reports_found": False,
            "is_scam": False,
            "classification": "LEGIT",
            "scam_comment_count": 0,
            "summary": "No scam or fraud reports found on Reddit for this company.",
            "bullet_points": [],
            "risk_level": "NONE"
        }
    
    # Prepare the prompt for Gemini
    comments_text = "\n\n---\n\n".join([
        f"Author: {c['author']}\nComment: {c['comment']}\nURL: {c['url']}"
        for c in comments
    ])
    
    prompt = f"""You are analyzing Reddit comments about internship experiences with the company "{company_name}".

Your task is to identify and summarize any reports of:
1. Fake or scam internships
2. Unpaid internships where payment was promised
3. Companies asking for money/deposits from interns
4. Fraudulent internship schemes
5. Any other red flags or warnings about the company

Here are the Reddit comments to analyze:

{comments_text}

Please provide:
1. A brief summary (2-3 sentences) of the overall sentiment
2. Specific bullet points listing each scam/fraud report with:
   - Type of issue (e.g., "Unpaid internship", "Asked for money", "Fake offer")
   - Brief description
   - Source (author if available)

Format your response as JSON with this structure:
{{
    "scam_reports_found": true/false,
    "summary": "brief summary here",
    "bullet_points": [
        {{
            "issue_type": "type of scam",
            "description": "what happened",
            "author": "reddit username or 'Anonymous'",
            "url": "comment url if available"
        }}
    ],
    "risk_level": "HIGH/MEDIUM/LOW/NONE"
}}

If no scam reports are found, set scam_reports_found to false and provide an appropriate summary.
"""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        
        # Parse the JSON response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        result['company_name'] = company_name
        result['total_comments_analyzed'] = len(comments)
        result['scam_comment_count'] = len(comments)
        
        # Classify as SCAM or LEGIT based on scam comment count
        if len(comments) >= 7:
            result['is_scam'] = True
            result['classification'] = "SCAM"
        else:
            result['is_scam'] = False
            result['classification'] = "LEGIT"
        
        return result
        
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        # Fallback to basic summary
        return {
            "company_name": company_name,
            "scam_reports_found": True,
            "summary": f"Found {len(comments)} potentially concerning comments about {company_name} on Reddit. Manual review recommended.",
            "bullet_points": [
                {
                    "issue_type": "Potential Issue",
                    "description": c['comment'][:200] + "..." if len(c['comment']) > 200 else c['comment'],
                    "author": c['author'],
                    "url": c['url']
                }
                for c in comments[:5]  # Limit to first 5
            ],
            "risk_level": "UNKNOWN",
            "total_comments_analyzed": len(comments),
            "scam_comment_count": len(comments),
            "is_scam": len(comments) >= 7,
            "classification": "SCAM" if len(comments) >= 7 else "LEGIT",
            "error": str(e)
        }


def check_company_internship_scams(company_name, output_dir=None, max_comments=15):
    """
    Main function to check for internship scam reports about a company
    
    Args:
        company_name: Name of the company to investigate
        output_dir: Directory to save results (optional)
        max_comments: Maximum number of comments to analyze
        
    Returns:
        dict: Summary of findings with bullet points
    """
    print(f"\n🔍 Searching for internship scam reports about: {company_name}")
    
    # Create output directory if specified
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    # Search queries focused on internship scams
    queries = [
        f'site:reddit.com "{company_name}" internship scam',
        f'site:reddit.com "{company_name}" fake internship',
        f'site:reddit.com "{company_name}" internship fraud money',
        f'site:reddit.com "{company_name}" internship not paid',
        f'site:reddit.com "{company_name}" internship warning'
    ]
    
    all_urls = []
    for query in queries:
        print(f"🔎 Query: {query}")
        urls = tavily_search(query, TAVILY_API_KEY, company_name, num_results=5)
        # Take only the first URL from each query that mentions the company
        if urls:
            all_urls.append(urls[0])
            print(f"   📌 Selected: {urls[0]}")
    
    # Remove duplicates
    all_urls = list(set(all_urls))
    print(f"\n📊 Total unique URLs to scrape: {len(all_urls)}")
    
    if not all_urls:
        result = {
            "company_name": company_name,
            "scam_reports_found": False,
            "is_scam": False,
            "classification": "LEGIT",
            "scam_comment_count": 0,
            "summary": "No Reddit discussions found about this company's internships.",
            "bullet_points": [],
            "risk_level": "NONE"
        }
        
        # Save result
        output_file = os.path.join(output_dir, f"{company_name.replace(' ', '_')}_scam_report.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result
    
    # Scrape comments from all URLs and filter by company name
    all_comments = []
    for url in all_urls:
        try:
            comments = scrape_reddit_post_with_company_filter(url, company_name)
            all_comments.extend(comments)
            
            # Stop if we have enough comments
            if len(all_comments) >= max_comments:
                print(f"\n✅ Reached target of {max_comments} comments, stopping...")
                break
            
            # Pause between requests to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
    
    print(f"\n📝 Total comments collected: {len(all_comments)}")
    
    # Filter for scam-related comments
    scam_comments = filter_scam_related_comments(all_comments, company_name)
    print(f"⚠️ Scam-related comments: {len(scam_comments)}")
    
    # Summarize with Gemini
    result = summarize_with_gemini(scam_comments, company_name)
    
    # Save result
    output_file = os.path.join(output_dir, f"{company_name.replace(' ', '_')}_scam_report.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Report saved to: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print(f"SCAM REPORT FOR: {company_name}")
    print("="*60)
    print(f"Classification: {result.get('classification', 'UNKNOWN')}")
    print(f"Scam Comment Count: {result.get('scam_comment_count', 0)}")
    print(f"Risk Level: {result.get('risk_level', 'UNKNOWN')}")
    print(f"Scam Reports Found: {result.get('scam_reports_found', False)}")
    print(f"\nSummary:\n{result.get('summary', 'No summary available')}")
    
    if result.get('bullet_points'):
        print("\nDetailed Findings:")
        for i, point in enumerate(result['bullet_points'], 1):
            print(f"\n{i}. {point.get('issue_type', 'Issue')}")
            print(f"   Description: {point.get('description', 'N/A')}")
            print(f"   Reported by: {point.get('author', 'Anonymous')}")
            if point.get('url'):
                print(f"   Source: {point['url']}")
    
    print("="*60 + "\n")
    
    return result


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        company_name = " ".join(sys.argv[1:])
    else:
        # Default test
        company_name = input("Enter company name to check for internship scams: ")
    
    result = check_company_internship_scams(company_name)