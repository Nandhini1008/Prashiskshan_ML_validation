"""
Reddit Scraper using ScraperAPI
Scrapes 4 standard URLs to test and extract comments
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ScraperAPI Configuration - Load from environment variables
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
SCRAPER_API_URL = os.getenv("SCRAPER_API_URL", "http://api.scraperapi.com")

# Test URLs
TEST_URLS = [
    "https://www.reddit.com/r/pune/comments/x1gvit/shinework_recruitment_scam/",
    "https://www.reddit.com/r/cscareerquestions/comments/12dmy0r/is_this_a_scam/",
    "https://www.reddit.com/r/developersIndia/comments/1eb3xft/kinda_unemployed_guy_roast_me_my_resume_my_skills/",
    "https://www.reddit.com/r/StartUpIndia/comments/1k45v26/i_think_my_backend_developer_intern_is_messing/"
]


def scrape_with_scraperapi(url):
    """
    Scrape a Reddit URL using ScraperAPI
    
    Args:
        url: Reddit URL to scrape
        
    Returns:
        dict: Extracted comments and metadata
    """
    print(f"\n{'='*80}")
    print(f"🕸️  SCRAPING: {url}")
    print(f"{'='*80}")
    
    try:
        # ScraperAPI parameters
        params = {
            'api_key': SCRAPER_API_KEY,
            'url': url,
            'render': 'true',  # Enable JavaScript rendering
            'country_code': 'us'  # Use US proxy
        }
        
        print("📡 Sending request to ScraperAPI...")
        response = requests.get(SCRAPER_API_URL, params=params, timeout=60)
        
        print(f"� Status Code: {response.status_code}")
        print(f"📄 Response length: {len(response.text)} characters")
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            return {
                'success': False,
                'error': f"HTTP {response.status_code}",
                'comments': []
            }
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save HTML for debugging
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_html')
        os.makedirs(debug_dir, exist_ok=True)
        
        url_safe = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        debug_file = os.path.join(debug_dir, f'{url_safe}_scraperapi.html')
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"💾 Saved HTML to: {debug_file}")
        
        # Extract comments
        comments = []
        
        # Method 1: Look for shreddit-comment elements
        shreddit_comments = soup.find_all('shreddit-comment')
        print(f"\n📊 Found {len(shreddit_comments)} <shreddit-comment> elements")
        
        for idx, comment_elem in enumerate(shreddit_comments):
            # Extract author
            author = 'Anonymous'
            author_link = comment_elem.find('a', href=lambda x: x and '/user/' in x)
            if author_link:
                author = author_link.get_text(strip=True)
            
            # Extract comment text
            text_divs = comment_elem.find_all('p')
            if text_divs:
                text = "\n".join([p.get_text(strip=True) for p in text_divs if p.get_text(strip=True)])
                if text:
                    comments.append({
                        'author': author,
                        'text': text,
                        'source': 'shreddit-comment',
                        'index': idx
                    })
        
        # Method 2: Look for post content
        post_divs = soup.find_all('div', id=lambda x: x and 'post-rtjson-content' in x)
        print(f"📊 Found {len(post_divs)} post content divs")
        
        for idx, post_div in enumerate(post_divs):
            text_p = post_div.find_all('p')
            if text_p:
                text = "\n".join([p.get_text(strip=True) for p in text_p if p.get_text(strip=True)])
                if text:
                    comments.append({
                        'author': 'OP',
                        'text': text,
                        'source': 'post-content',
                        'index': idx
                    })
        
        # Method 3: Look for comment divs with specific classes
        comment_divs = soup.find_all('div', class_=lambda x: x and 'scalable-text' in x)
        print(f"📊 Found {len(comment_divs)} divs with scalable-text class")
        
        for idx, div in enumerate(comment_divs):
            text_p = div.find_all('p')
            if text_p:
                text = "\n".join([p.get_text(strip=True) for p in text_p if p.get_text(strip=True)])
                if text and not any(c['text'] == text for c in comments):  # Avoid duplicates
                    comments.append({
                        'author': 'Anonymous',
                        'text': text,
                        'source': 'scalable-text-div',
                        'index': idx
                    })
        
        # Print results
        print(f"\n✅ EXTRACTED {len(comments)} comments/posts")
        if comments:
            print("\n📝 Sample content:")
            for i, comment in enumerate(comments[:3], 1):
                print(f"\n{i}. Author: {comment['author']} [{comment['source']}]")
                preview = comment['text'][:150] + '...' if len(comment['text']) > 150 else comment['text']
                print(f"   {preview}")
        else:
            print("\n❌ NO CONTENT EXTRACTED!")
            print("\n🔍 Checking page title...")
            title = soup.find('title')
            if title:
                print(f"   Page title: {title.get_text()}")
        
        return {
            'success': True,
            'comment_count': len(comments),
            'comments': comments
        }
        
    except requests.exceptions.Timeout:
        print(f"\n❌ ERROR: Request timed out")
        return {
            'success': False,
            'error': 'Timeout',
            'comments': []
        }
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'comments': []
        }


def main():
    """Test scraping on standard URLs using ScraperAPI"""
    print("\n" + "="*80)
    print("REDDIT SCRAPER TEST - Using ScraperAPI")
    print("="*80)
    print(f"API Key: {SCRAPER_API_KEY[:10]}...")
    
    all_results = {}
    
    for url in TEST_URLS:
        result = scrape_with_scraperapi(url)
        all_results[url] = result
        
        # Pause between requests to avoid rate limiting
        print("\n⏳ Waiting 3 seconds before next request...")
        time.sleep(3)
    
    # Save results
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_results_scraperapi.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")
    
    total_comments = 0
    successful = 0
    
    for url, result in all_results.items():
        url_short = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        status = "✅" if result['success'] else "❌"
        count = result.get('comment_count', 0)
        total_comments += count
        if result['success']:
            successful += 1
        
        error_msg = f" - {result.get('error', '')}" if not result['success'] else ""
        print(f"{status} {url_short}: {count} comments{error_msg}")
    
    print(f"\n� Total: {successful}/{len(TEST_URLS)} URLs successful")
    print(f"📊 Total comments extracted: {total_comments}")
    print(f"\n�💾 Full results saved to: {output_file}")
    print(f"💾 HTML files saved to: debug_html/")
    
    if total_comments == 0:
        print("\n⚠️  WARNING: No comments extracted from any URL!")
        print("   Possible reasons:")
        print("   1. ScraperAPI key might be invalid")
        print("   2. Reddit might be blocking the requests")
        print("   3. Page structure might have changed")
        print("\n   Check the saved HTML files to see what was returned.")
    else:
        print(f"\n✅ SUCCESS: Extracted {total_comments} total comments")


if __name__ == "__main__":
    main()