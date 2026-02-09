from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Header
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import re
import asyncio
import csv
import io
import json
import secrets
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class ScrapedData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_url: str
    domain: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    contact_number: Optional[str] = None
    mobile_number: Optional[str] = None
    stage: Optional[str] = None
    focus_industry: Optional[str] = None
    focus_sector: Optional[str] = None
    service_area: Optional[str] = None
    location: Optional[str] = None
    active_years: Optional[str] = None
    engagement_level: Optional[str] = None
    active_on_portal: Optional[str] = None
    name: Optional[str] = None
    about_company: Optional[str] = None
    status: str = "success"  # success, failed, partial
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScrapeRequest(BaseModel):
    url: str

class BulkScrapeRequest(BaseModel):
    urls: List[str]

class APIKey(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    is_active: bool = True

class APIKeyCreate(BaseModel):
    name: str

# Helper Functions for Scraping
def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(email_pattern, text)))

def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text"""
    # Indian phone number patterns
    patterns = [
        r'\+91[\s-]?\d{10}',
        r'\d{10}',
        r'\(\d{3}\)[\s-]?\d{3}[\s-]?\d{4}',
        r'\d{3}[\s-]\d{3}[\s-]\d{4}'
    ]
    phones = []
    for pattern in patterns:
        phones.extend(re.findall(pattern, text))
    return list(set(phones))

async def scrape_with_beautifulsoup(url: str) -> Dict[str, Any]:
    """Fallback scraping using BeautifulSoup and requests"""
    logger.info(f"Using BeautifulSoup fallback for URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {}
        all_text = soup.get_text()
        
        logger.info(f"Page content length: {len(response.content)} bytes")
        
        # Try to find elements by ID and navigate the DOM structure
        # Name extraction
        try:
            txt_editor = soup.find(id='txtEditor')
            if txt_editor:
                name_elem = txt_editor.select_one('div > div:nth-of-type(2) > div:nth-of-type(2) > div > div > div:nth-of-type(2) > div:nth-of-type(2) > p')
                if name_elem:
                    data['name'] = name_elem.get_text(strip=True)
                    logger.info(f"Extracted name: {data['name']}")
        except Exception as e:
            logger.warning(f"Could not extract name: {e}")
        
        # Website extraction
        try:
            txt_editor = soup.find(id='txtEditor')
            if txt_editor:
                website_elem = txt_editor.select_one('div > div:nth-of-type(2) > div:nth-of-type(2) > div > div > div:nth-of-type(2) > div:nth-of-type(2) > span:nth-of-type(3) > a')
                if website_elem and website_elem.get('href'):
                    data['website'] = website_elem.get('href')
                    logger.info(f"Extracted website: {data['website']}")
                    # Extract domain
                    domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', data['website'])
                    if domain_match:
                        data['domain'] = domain_match.group(1)
        except Exception as e:
            logger.warning(f"Could not extract website: {e}")
        
        # Email extraction
        try:
            txt_editor = soup.find(id='txtEditor')
            if txt_editor:
                email_elem = txt_editor.select_one('div > div:nth-of-type(2) > div:nth-of-type(2) > div > div > div:nth-of-type(2) > div:nth-of-type(2) > span:nth-of-type(2)')
                if email_elem:
                    email_text = email_elem.get_text(strip=True)
                    if '@' in email_text:
                        data['email'] = email_text
                        logger.info(f"Extracted email: {data['email']}")
        except Exception as e:
            logger.warning(f"Could not extract email: {e}")
        
        # Contact number extraction
        try:
            txt_editor = soup.find(id='txtEditor')
            if txt_editor:
                contact_elem = txt_editor.select_one('div > div:nth-of-type(2) > div:nth-of-type(2) > div > div > div:nth-of-type(2) > div:nth-of-type(2) > span:nth-of-type(1)')
                if contact_elem:
                    contact_text = contact_elem.get_text(strip=True)
                    if contact_text and contact_text not in ['×', '—', '-', 'N/A', 'XXXXXXX', '0000000000']:
                        data['contact_number'] = contact_text
                        data['mobile_number'] = contact_text
                        logger.info(f"Extracted contact: {contact_text}")
        except Exception as e:
            logger.warning(f"Could not extract contact: {e}")
        
        # Other fields from the second section
        try:
            section = soup.find(id='1638164275868262-0')
            if section:
                spans = section.select('div > div > div > div > div > div > div:nth-of-type(2) > div > div > div > div > span')
                
                # Try to extract fields by position
                for i, span in enumerate(spans, 1):
                    span_text = span.select_one('span:nth-of-type(2)')
                    if span_text:
                        value = span_text.get_text(strip=True)
                        if value and value not in ['×', '—', '-', 'N/A', '']:
                            if i == 1:
                                data['stage'] = value
                            elif i == 2:
                                data['focus_industry'] = value
                            elif i == 3:
                                data['focus_sector'] = value
                            elif i == 4:
                                data['service_area'] = value
                            elif i == 5:
                                data['location'] = value
                            elif i == 6:
                                # Active years might have a <p> tag
                                p_elem = span_text.find('p')
                                if p_elem:
                                    data['active_years'] = p_elem.get_text(strip=True)
                                else:
                                    data['active_years'] = value
                
                # About company
                about_elem = section.select_one('div > div > div > div > div > div > div:nth-of-type(1) > div > div:nth-of-type(1)')
                if about_elem:
                    about_text = about_elem.get_text(strip=True)
                    if about_text and len(about_text) > 10:
                        data['about_company'] = about_text
                        logger.info(f"Extracted about_company: {about_text[:100]}...")
        except Exception as e:
            logger.warning(f"Could not extract secondary fields: {e}")
        
        # Engagement level
        try:
            txt_editor = soup.find(id='txtEditor')
            if txt_editor:
                engagement_elem = txt_editor.select_one('div > div:nth-of-type(2) > div:nth-of-type(2) > div > div > div:nth-of-type(2) > div:nth-of-type(2) > h6:nth-of-type(1) > span > strong')
                if engagement_elem:
                    engagement_text = engagement_elem.get_text(strip=True)
                    if engagement_text:
                        data['engagement_level'] = engagement_text
                        data['active_on_portal'] = engagement_text
                        logger.info(f"Extracted engagement: {engagement_text}")
        except Exception as e:
            logger.warning(f"Could not extract engagement: {e}")
        
        # Regex fallback for missing critical fields
        if not data.get('name'):
            company_patterns = [
                r'([A-Z][A-Z\s&]+(?:LLP|PRIVATE LIMITED|PVT\.? LTD\.?|LIMITED|LTD\.?))',
                r'Company Name:?\s*([A-Z][A-Za-z\s&]+(?:LLP|Pvt|Ltd|Limited))',
            ]
            for pattern in company_patterns:
                match = re.search(pattern, all_text)
                if match:
                    potential_name = match.group(1).strip()
                    if len(potential_name) > 5:
                        data['name'] = potential_name
                        break
        
        if not data.get('email'):
            emails = extract_emails(all_text)
            if emails:
                valid_emails = [e for e in emails if not any(x in e.lower() for x in [
                    'example', 'test', 'noreply', 'xxxx', 'xxx@', '@startupindia', '@gov'
                ])]
                if valid_emails:
                    data['email'] = valid_emails[0]
        
        if not data.get('website'):
            website_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+\.com[^\s<>"]*'
            website_matches = re.findall(website_pattern, all_text)
            if website_matches:
                valid_websites = [w for w in website_matches if not any(x in w.lower() for x in [
                    'startupindia', 'google', 'facebook', 'linkedin', 'twitter', '.js', '.css'
                ])]
                if valid_websites:
                    data['website'] = valid_websites[0]
                    domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', data['website'])
                    if domain_match:
                        data['domain'] = domain_match.group(1)
        
        logger.info(f"BeautifulSoup extracted {len(data)} fields: {list(data.keys())}")
        return data
    except Exception as e:
        logger.error(f"BeautifulSoup fallback also failed: {e}", exc_info=True)
        return {}

async def scrape_startup_india_page(url: str) -> Dict[str, Any]:
    """Scrape startup India portal page using Playwright with XPath selectors, fallback to BeautifulSoup"""
    playwright_failed = False
    
    try:
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(
                headless=True,
                executable_path='/pw-browsers/chromium-1208/chrome-linux64/chrome',
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            
            # Create a new page with viewport
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # Set user agent to avoid bot detection
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            })
            
            # Navigate to the URL
            logger.info(f"Navigating to URL with Playwright: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for content to load - give enough time for JavaScript to render
            logger.info("Waiting for content to load...")
            await asyncio.sleep(12)
            
            # Try to wait for main content area
            try:
                await page.wait_for_selector('#txtEditor, [id*="1638164275868262"]', timeout=5000)
            except PlaywrightTimeoutError:
                logger.warning("Timeout waiting for main content selectors, continuing anyway...")
            
            data = {}
            
            # XPath configuration for field extraction
            xpaths = {
                'name': '//*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/p',
                'website': '//*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[3]/a',
                'email': '//*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[2]',
                'contact_number': '//*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[1]',
                'stage': '//*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[1]/span[2]',
                'focus_industry': '//*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[2]/span[2]',
                'focus_sector': '//*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[3]/span[2]',
                'service_area': '//*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[4]/span[2]',
                'location': '//*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[5]/span[2]',
                'active_years': '//*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[6]/span[2]/p',
                'engagement_level': '//*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/h6[1]/span/strong',
                'about_company': '//*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[1]/div/div[1]'
            }
            
            # Extract data using XPath selectors
            for field, xpath in xpaths.items():
                try:
                    # Use Playwright's locator with xpath
                    element = page.locator(f'xpath={xpath}').first
                    
                    # Check if element exists
                    if await element.count() > 0:
                        # Get text content or href for links
                        if field == 'website':
                            value = await element.get_attribute('href')
                        else:
                            value = await element.text_content()
                        
                        if value:
                            value = value.strip()
                            # Filter out invalid values
                            if value and value not in ['×', '—', '-', 'N/A', '', 'XXXXXXX', '0000000000', 'NA']:
                                data[field] = value
                                logger.info(f"Extracted {field}: {value}")
                except Exception as e:
                    logger.warning(f"Could not extract {field} using XPath: {e}")
            
            # Special handling for mobile_number (same XPath as contact_number)
            if data.get('contact_number'):
                data['mobile_number'] = data['contact_number']
            
            # Special handling for active_on_portal (same XPath as engagement_level)
            if data.get('engagement_level'):
                data['active_on_portal'] = data['engagement_level']
            
            # Extract domain from website if website exists
            if data.get('website'):
                try:
                    # Clean up website URL
                    website_url = data['website']
                    if not website_url.startswith('http'):
                        website_url = 'https://' + website_url
                    
                    # Extract domain
                    domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', website_url)
                    if domain_match:
                        data['domain'] = domain_match.group(1)
                        data['website'] = website_url  # Store cleaned URL
                except Exception as e:
                    logger.warning(f"Error extracting domain: {e}")
            
            # Fallback: if XPath extraction failed for critical fields, try regex patterns on page text
            if not data.get('name') or not data.get('email') or not data.get('website'):
                logger.info("Some fields missing, attempting fallback extraction...")
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                all_text = soup.get_text()
                
                # Company name fallback
                if not data.get('name'):
                    company_patterns = [
                        r'([A-Z][A-Z\s&]+(?:LLP|PRIVATE LIMITED|PVT\.? LTD\.?|LIMITED|LTD\.?))',
                        r'Company Name:?\s*([A-Z][A-Za-z\s&]+(?:LLP|Pvt|Ltd|Limited))',
                    ]
                    for pattern in company_patterns:
                        match = re.search(pattern, all_text)
                        if match:
                            potential_name = match.group(1).strip()
                            if len(potential_name) > 5:
                                data['name'] = potential_name
                                logger.info(f"Extracted name via fallback: {potential_name}")
                                break
                
                # Email fallback
                if not data.get('email'):
                    emails = extract_emails(all_text)
                    if emails:
                        valid_emails = [e for e in emails if not any(x in e.lower() for x in [
                            'example', 'test', 'noreply', 'xxxx', 'xxx@', 
                            '@startupindia', '@gov', '@facebook', '@twitter'
                        ])]
                        if valid_emails:
                            data['email'] = valid_emails[0]
                            logger.info(f"Extracted email via fallback: {valid_emails[0]}")
                
                # Website fallback
                if not data.get('website'):
                    website_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+\.com[^\s<>"]*'
                    website_matches = re.findall(website_pattern, all_text)
                    if website_matches:
                        valid_websites = [w for w in website_matches if not any(x in w.lower() for x in [
                            'startupindia', 'google', 'facebook', 'linkedin', 'twitter', '.js', '.css'
                        ])]
                        if valid_websites:
                            data['website'] = valid_websites[0]
                            logger.info(f"Extracted website via fallback: {valid_websites[0]}")
                            # Extract domain
                            domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', data['website'])
                            if domain_match:
                                data['domain'] = domain_match.group(1)
            
            # Close browser
            await browser.close()
            
            logger.info(f"Playwright extracted {len(data)} fields successfully")
            return data
            
    except Exception as e:
        logger.error(f"Playwright scraping failed: {e}", exc_info=True)
        playwright_failed = True
    
    # If Playwright failed, try BeautifulSoup fallback
    if playwright_failed:
        logger.info("Falling back to BeautifulSoup scraping...")
        return await scrape_with_beautifulsoup(url)

async def scrape_website_details(website_url: str) -> Dict[str, Any]:
    """Scrape additional details from company website using Playwright for better JavaScript support"""
    try:
        if not website_url.startswith('http'):
            website_url = 'https://' + website_url
        
        logger.info(f"Scraping website: {website_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path='/pw-browsers/chromium-1208/chrome-linux64/chrome',
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # Set user agent
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            try:
                # Navigate to website with timeout
                await page.goto(website_url, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(3)  # Wait for content to render
                
                html_content = await page.content()
                await browser.close()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                data = {}
                
                # Get all text
                all_text = soup.get_text()
                
                # Extract about section
                about_section = soup.find(['section', 'div'], class_=re.compile('about|description|overview|company-info', re.I))
                if about_section:
                    about_text = about_section.get_text(strip=True)
                    # Clean up the text
                    about_text = ' '.join(about_text.split())  # Remove extra whitespace
                    if about_text and len(about_text) > 20:
                        data['about_company'] = about_text[:1000] if len(about_text) > 1000 else about_text
                        logger.info(f"Extracted about section: {data['about_company'][:100]}...")
                
                # Extract contact info
                emails = extract_emails(all_text)
                if emails:
                    # Filter out common false positives
                    valid_emails = [e for e in emails if not any(x in e.lower() for x in [
                        'example', 'test', 'noreply', 'support@wix', 'example.com'
                    ])]
                    if valid_emails:
                        data['email'] = valid_emails[0]
                        logger.info(f"Extracted email from website: {data['email']}")
                
                phones = extract_phone_numbers(all_text)
                if phones:
                    # Filter out obviously fake numbers
                    valid_phones = [p for p in phones if (
                        len(p) >= 10 and 
                        p not in ['0000000000', '1111111111', '9999999999']
                    )]
                    if valid_phones:
                        data['contact_number'] = valid_phones[0] if len(valid_phones) > 0 else None
                        data['mobile_number'] = valid_phones[1] if len(valid_phones) > 1 else None
                        logger.info(f"Extracted phone numbers from website")
                
                # Extract location from footer or contact section
                contact_section = soup.find(['section', 'div', 'footer'], class_=re.compile('contact|footer|address|location', re.I))
                if contact_section:
                    contact_text = contact_section.get_text()
                    # Look for location patterns
                    location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+)', contact_text)
                    if location_match:
                        data['location'] = location_match.group(1)
                        logger.info(f"Extracted location from website: {data['location']}")
                
                logger.info(f"Successfully scraped website with {len(data)} fields")
                return data
                
            except Exception as e:
                logger.error(f"Error loading website {website_url}: {e}")
                await browser.close()
                return {}
                
    except Exception as e:
        logger.error(f"Error scraping website: {e}")
        return {}

async def scrape_url(url: str) -> ScrapedData:
    """Main scraping function"""
    try:
        # First scrape the startup India page
        startup_data = await scrape_startup_india_page(url)
        
        # If website found, scrape additional details from the company website
        if startup_data.get('website'):
            logger.info(f"Website found: {startup_data['website']}, crawling for additional details...")
            website_data = await scrape_website_details(startup_data['website'])
            # Merge data, preferring startup_data for conflicts (startup data is more reliable)
            for key, value in website_data.items():
                if not startup_data.get(key) and value:
                    startup_data[key] = value
                    logger.info(f"Added {key} from website scraping")
        
        scraped = ScrapedData(
            source_url=url,
            **startup_data
        )
        
        # Save to database
        doc = scraped.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.scraped_data.insert_one(doc)
        logger.info(f"Successfully saved scraped data for {url}")
        
        return scraped
    except Exception as e:
        logger.error(f"Error in scrape_url: {e}", exc_info=True)
        error_data = ScrapedData(
            source_url=url,
            status="failed",
            error_message=str(e)
        )
        doc = error_data.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.scraped_data.insert_one(doc)
        return error_data

# API Key verification
async def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key from Authorization header"""
    if authorization is None:
        raise HTTPException(
            status_code=401, 
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization format. Use 'Bearer YOUR_API_KEY'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    api_key = authorization.replace("Bearer ", "")
    
    # Check if key exists and is active
    key_doc = await db.api_keys.find_one({"key": api_key, "is_active": True}, {"_id": 0})
    if not key_doc:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Update last used timestamp
    await db.api_keys.update_one(
        {"key": api_key},
        {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
    )
    
    return key_doc

# Routes
@api_router.get("/")
async def root():
    return {"message": "Data Scraping API", "version": "1.0.0"}

@api_router.post("/scrape", response_model=ScrapedData)
async def scrape_single_url(request: ScrapeRequest):
    """Scrape a single URL"""
    await asyncio.sleep(0.5)  # Rate limiting
    return await scrape_url(request.url)

@api_router.post("/scrape/bulk", response_model=List[ScrapedData])
async def scrape_bulk_urls(request: BulkScrapeRequest):
    """Scrape multiple URLs with rate limiting"""
    results = []
    for url in request.urls:
        result = await scrape_url(url)
        results.append(result)
        await asyncio.sleep(1)  # Rate limiting between requests
    return results

@api_router.post("/scrape/upload-csv")
async def upload_csv_for_scraping(file: UploadFile = File(...)):
    """Upload CSV file with URLs and scrape them"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        contents = await file.read()
        csv_file = io.StringIO(contents.decode('utf-8'))
        reader = csv.DictReader(csv_file)
        
        urls = []
        for row in reader:
            # Look for URL in common column names
            url = row.get('url') or row.get('URL') or row.get('link') or row.get('Link')
            if url:
                urls.append(url)
        
        if not urls:
            raise HTTPException(status_code=400, detail="No URLs found in CSV. Please ensure there's a column named 'url', 'URL', 'link', or 'Link'")
        
        # Start scraping
        results = []
        for url in urls:
            result = await scrape_url(url)
            results.append(result.model_dump())
            await asyncio.sleep(1)  # Rate limiting
        
        return {"total": len(urls), "results": results}
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/results", response_model=List[ScrapedData])
async def get_all_results(limit: int = 100, skip: int = 0):
    """Get all scraped results"""
    results = await db.scraped_data.find({}, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    # Convert ISO string timestamps back to datetime
    for result in results:
        if isinstance(result.get('timestamp'), str):
            result['timestamp'] = datetime.fromisoformat(result['timestamp'])
    
    return results

@api_router.get("/results/{result_id}", response_model=ScrapedData)
async def get_result_by_id(result_id: str):
    """Get a specific result by ID"""
    result = await db.scraped_data.find_one({"id": result_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if isinstance(result.get('timestamp'), str):
        result['timestamp'] = datetime.fromisoformat(result['timestamp'])
    
    return result

@api_router.get("/export/csv")
async def export_results_csv(limit: int = 1000):
    """Export results to CSV"""
    results = await db.scraped_data.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    
    # Create CSV in memory
    output = io.StringIO()
    fieldnames = ['id', 'source_url', 'name', 'domain', 'website', 'email', 'contact_number', 
                  'mobile_number', 'stage', 'focus_industry', 'focus_sector', 'service_area', 
                  'location', 'active_years', 'engagement_level', 'active_on_portal', 
                  'about_company', 'status', 'error_message', 'timestamp']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for result in results:
        writer.writerow({k: result.get(k, '') for k in fieldnames})
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scraped_data.csv"}
    )

@api_router.get("/export/json")
async def export_results_json(limit: int = 1000):
    """Export results to JSON"""
    results = await db.scraped_data.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    
    return StreamingResponse(
        iter([json.dumps(results, indent=2, default=str)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=scraped_data.json"}
    )

# API Key Management
@api_router.post("/api-keys", response_model=APIKey)
async def create_api_key(request: APIKeyCreate):
    """Create a new API key"""
    api_key = APIKey(
        key=f"sk_{secrets.token_urlsafe(32)}",
        name=request.name
    )
    
    doc = api_key.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('last_used'):
        doc['last_used'] = doc['last_used'].isoformat()
    
    await db.api_keys.insert_one(doc)
    return api_key

@api_router.get("/api-keys", response_model=List[APIKey])
async def get_api_keys():
    """Get all API keys"""
    keys = await db.api_keys.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for key in keys:
        if isinstance(key.get('created_at'), str):
            key['created_at'] = datetime.fromisoformat(key['created_at'])
        if key.get('last_used') and isinstance(key['last_used'], str):
            key['last_used'] = datetime.fromisoformat(key['last_used'])
    
    return keys

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    """Deactivate an API key"""
    result = await db.api_keys.update_one(
        {"id": key_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": "API key deactivated"}

# Protected API endpoints (require bearer token)
@api_router.post("/protected/scrape", response_model=ScrapedData)
async def protected_scrape_single(request: ScrapeRequest, key=Depends(verify_api_key)):
    """Protected endpoint: Scrape a single URL"""
    await asyncio.sleep(0.5)
    return await scrape_url(request.url)

@api_router.post("/protected/scrape/bulk", response_model=List[ScrapedData])
async def protected_scrape_bulk(request: BulkScrapeRequest, key=Depends(verify_api_key)):
    """Protected endpoint: Scrape multiple URLs"""
    results = []
    for url in request.urls:
        result = await scrape_url(url)
        results.append(result)
        await asyncio.sleep(1)
    return results

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()