import requests
from bs4 import BeautifulSoup
import re
import logging
import html
import urllib.parse

logger = logging.getLogger(__name__)

class ScraperException(Exception): pass

class AmazonScraper:
    def __init__(self):
        self.api_key = os.getenv("SCRAPERAPI_KEY")
        self.endpoint = "http://api.scraperapi.com"

    def scrape(self, url: str):
        url = html.unescape(url).strip().split('?')[0]
        
        asin_match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
        if asin_match:
            asin = asin_match.group(1)
            # Use the main product page but for mobile (often bypasses the sign-in wall)
            target_url = f"https://www.amazon.in/dp/{asin}/"
            logger.info(f"Targeting ASIN: {asin} via Mobile View")
        else:
            target_url = url

        response = self._fetch_page(target_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        print("soup",soup.prettify()[:2000])  # Print first 1000 chars of the soup for debugging
        
        page_title = soup.title.string if soup.title else "No Title"
        logger.info(f"Page Title received: {page_title}")
        global_storage = None
        global_color = None
        
        # Extract Storage (matches 128GB, 64 GB, etc.)
        storage_match = re.search(r'(\d+\s*(?:GB|TB))', page_title, re.IGNORECASE)
        if storage_match:
            global_storage = storage_match.group(1).strip()
            
        # Extract Color (matches everything after '-' and before ':')
        color_match = re.search(r'-\s*([^:]+)', page_title)
        if color_match:
            global_color = color_match.group(1).strip()

        if "Sign-In" in page_title or "Robot Check" in page_title:
            logger.error("Amazon redirected to Sign-In or CAPTCHA.")
            raise ScraperException("Amazon is demanding a login. Proxy rotation or Premium residential IPs needed.")

        reviews = self._parse_reviews(soup, global_storage, global_color)
        return reviews

    def _fetch_page(self, url: str):
        encoded_url = urllib.parse.quote(url)
        # CHANGE: Added device_type=mobile
        scraper_url = (
            f"{self.endpoint}?api_key={self.api_key}"
            f"&url={encoded_url}"
            f"&country_code=in"
            f"&render=true"
            f"&premium=true"
            f"&device_type=mobile" 
        )
        
        try:
            logger.info("Requesting through ScraperAPI (Mobile Render)...")
            response = requests.get(scraper_url, timeout=120)
            response.raise_for_status()
            print("res",response.text[:1000])  # Print first 500 chars of the response for debugging
            return response
        except Exception as e:
            logger.error(f"ScraperAPI Error: {str(e)}")
            raise ScraperException(f"Network error: {str(e)}")

    def _parse_reviews(self, soup, storage_text, color_text):
        reviews = []
        review_elements = soup.select('[id^="customer_review-"]') 
        
        if not review_elements:
            review_elements = soup.find_all('div', {'data-hook': 'review'})

        logger.info(f"Found {len(review_elements)} review containers.")

        for item in review_elements:
            try:
                # --- TEXT ---
                body = item.select_one('.review-text-content') or item.find('span', {'data-hook': 'review-body'})
                text = body.get_text(strip=True) if body else ""
                
                # --- TITLE ---
                title_node = (
                    item.select_one('.review-title-content') or 
                    item.select_one('.review-title') or 
                    item.find('span', class_='a-text-bold') or
                    item.find('a', {'data-hook': 'review-title'})
                )
                title = title_node.get_text(strip=True) if title_node else ""
                
                # --- RATING ---
                rating_node = item.select_one('.review-rating') or item.find('i', {'data-hook': 'review-star-rating'})
                rating = 0
                if rating_node:
                    rating_text = rating_node.get_text()
                    match = re.search(r'(\d)', rating_text)
                    rating = int(match.group(1)) if match else 0

               

                if text:
                    reviews.append({
                        "title": title,
                        "text": text,
                        "rating": rating,
                        "storage": storage_text,
                        "color": color_text,
                        "verified": "Verified" in item.get_text()
                    })
            except Exception as e:
                logger.error(f"Error parsing individual review: {str(e)}")
                continue

        return reviews