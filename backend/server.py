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

async def scrape_startup_india_page(url: str) -> Dict[str, Any]:
    """Scrape startup India portal page using Playwright for JavaScript-rendered content"""
    try:
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create a new page
            page = await browser.new_page()
            
            # Set user agent to avoid bot detection
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Navigate to the URL
            logger.info(f"Navigating to URL: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for content to load - increase delay to allow JavaScript to render
            logger.info("Waiting for content to load...")
            await asyncio.sleep(5)  # 5 second delay to ensure content loads
            
            # Try to wait for specific content indicators
            try:
                # Wait for main content area (adjust selector based on actual page structure)
                await page.wait_for_selector('body', timeout=10000)
            except PlaywrightTimeoutError:
                logger.warning("Timeout waiting for body selector, continuing anyway...")
            
            # Get the fully rendered HTML
            html_content = await page.content()
            
            # Close browser
            await browser.close()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            data = {}
            
            # Extract name
            name_elem = soup.find('h1') or soup.find('h2', class_=re.compile('name|title', re.I))
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)
            
            # Extract all text for parsing
            all_text = soup.get_text()
            
            # Log a snippet of the content for debugging
            logger.info(f"Page content length: {len(html_content)} chars")
            logger.info(f"First 500 chars of text: {all_text[:500]}")
            
            # Extract structured data from the page
            labels = soup.find_all(['dt', 'label', 'span', 'div'], class_=re.compile('label|key|field', re.I))
            for label in labels:
                label_text = label.get_text(strip=True).lower()
                value_elem = label.find_next_sibling() or label.parent.find_next('dd') or label.find_next('span')
                
                if value_elem:
                    value = value_elem.get_text(strip=True)
                    
                    if 'website' in label_text or 'url' in label_text:
                        data['website'] = value
                    elif 'email' in label_text:
                        data['email'] = value
                    elif 'phone' in label_text or 'contact' in label_text or 'mobile' in label_text:
                        if 'mobile' in label_text:
                            data['mobile_number'] = value
                        else:
                            data['contact_number'] = value
                    elif 'stage' in label_text:
                        data['stage'] = value
                    elif 'industry' in label_text:
                        data['focus_industry'] = value
                    elif 'sector' in label_text:
                        data['focus_sector'] = value
                    elif 'service' in label_text:
                        data['service_area'] = value
                    elif 'location' in label_text or 'address' in label_text or 'city' in label_text:
                        data['location'] = value
                    elif 'year' in label_text or 'active' in label_text:
                        data['active_years'] = value
                    elif 'engagement' in label_text:
                        data['engagement_level'] = value
                    elif 'portal' in label_text:
                        data['active_on_portal'] = value
            
            # Extract emails and phones from full text if not found
            if not data.get('email'):
                emails = extract_emails(all_text)
                if emails:
                    data['email'] = emails[0]
            
            if not data.get('contact_number') and not data.get('mobile_number'):
                phones = extract_phone_numbers(all_text)
                if phones:
                    data['contact_number'] = phones[0] if len(phones) > 0 else None
                    data['mobile_number'] = phones[1] if len(phones) > 1 else None
            
            # Extract domain
            if data.get('website'):
                domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', data['website'])
                if domain_match:
                    data['domain'] = domain_match.group(1)
            
            logger.info(f"Extracted data: {data}")
            return data
    except Exception as e:
        logger.error(f"Error scraping startup page: {e}", exc_info=True)
        raise

def scrape_website_details(website_url: str) -> Dict[str, Any]:
    """Scrape additional details from company website"""
    try:
        if not website_url.startswith('http'):
            website_url = 'https://' + website_url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(website_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {}
        
        # Get all text
        all_text = soup.get_text()
        
        # Extract about section
        about_section = soup.find(['section', 'div'], class_=re.compile('about|description|overview', re.I))
        if about_section:
            about_text = about_section.get_text(strip=True)
            data['about_company'] = about_text[:500] if len(about_text) > 500 else about_text
        
        # Extract contact info
        emails = extract_emails(all_text)
        if emails:
            data['email'] = emails[0]
        
        phones = extract_phone_numbers(all_text)
        if phones:
            data['contact_number'] = phones[0] if len(phones) > 0 else None
            data['mobile_number'] = phones[1] if len(phones) > 1 else None
        
        # Extract location from footer or contact section
        contact_section = soup.find(['section', 'div', 'footer'], class_=re.compile('contact|footer|address', re.I))
        if contact_section:
            contact_text = contact_section.get_text()
            # Look for location patterns
            location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+)', contact_text)
            if location_match:
                data['location'] = location_match.group(1)
        
        return data
    except Exception as e:
        logger.error(f"Error scraping website: {e}")
        return {}

async def scrape_url(url: str) -> ScrapedData:
    """Main scraping function"""
    try:
        # First scrape the startup India page (now async)
        startup_data = await scrape_startup_india_page(url)
        
        # If website found, scrape additional details
        if startup_data.get('website'):
            website_data = await asyncio.to_thread(scrape_website_details, startup_data['website'])
            # Merge data, preferring startup_data for conflicts
            for key, value in website_data.items():
                if not startup_data.get(key) and value:
                    startup_data[key] = value
        
        scraped = ScrapedData(
            source_url=url,
            **startup_data
        )
        
        # Save to database
        doc = scraped.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.scraped_data.insert_one(doc)
        
        return scraped
    except Exception as e:
        logger.error(f"Error in scrape_url: {e}")
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