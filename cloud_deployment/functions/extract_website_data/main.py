"""
Cloud Function: Website Data Extraction
Web sitelerinden veri çıkarır ve Cloud Storage'a kaydeder.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List
import functions_framework
from google.cloud import storage
from google.cloud import pubsub_v1
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re

# Logging ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
BUCKET_NAME = os.environ.get('STORAGE_BUCKET_NAME')
PUBSUB_TOPIC = os.environ.get('PUBSUB_TOPIC', 'ai-overview-pipeline')

class CloudWebsiteDataExtractor:
    """Cloud-based website data extractor"""
    
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        
    def discover_urls(self, base_url: str, max_pages: int = 100) -> List[str]:
        """URL'leri keşfet"""
        discovered_urls = set()
        to_crawl = [base_url]
        crawled = set()
        
        headers = {
            'User-Agent': 'AI-Overview-Bot/1.0'
        }
        
        while to_crawl and len(discovered_urls) < max_pages:
            current_url = to_crawl.pop(0)
            
            if current_url in crawled:
                continue
                
            try:
                logger.info(f"Crawling: {current_url}")
                response = requests.get(current_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Bu sayfayı ekle
                    discovered_urls.add(current_url)
                    crawled.add(current_url)
                    
                    # Link'leri bul
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(current_url, href)
                        
                        # Aynı domain kontrolü
                        if urlparse(full_url).netloc == urlparse(base_url).netloc:
                            # Exclusion patterns kontrolü
                            if not self._should_exclude_url(full_url):
                                if full_url not in discovered_urls and full_url not in crawled:
                                    to_crawl.append(full_url)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Error crawling {current_url}: {str(e)}")
                continue
        
        return list(discovered_urls)
    
    def _should_exclude_url(self, url: str) -> bool:
        """URL'yi exclude etmeli mi?"""
        exclude_patterns = [
            r'.*\.(pdf|doc|docx|xls|xlsx|ppt|pptx)$',
            r'.*\.(jpg|jpeg|png|gif|svg|ico)$',
            r'.*\.(zip|rar|tar|gz)$',
            r'.*\.(mp3|mp4|avi|mov|wmv)$',
            r'.*/admin/.*',
            r'.*/wp-admin/.*',
            r'.*/login.*',
            r'.*/register.*',
            r'.*\?.*print.*',
            r'.*#.*',
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def extract_content_from_urls(self, urls: List[str]) -> List[Dict]:
        """URL'lerden içerik çıkar"""
        extracted_data = []
        
        headers = {
            'User-Agent': 'AI-Overview-Bot/1.0'
        }
        
        for url in urls:
            try:
                logger.info(f"Extracting content from: {url}")
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Title
                    title_tag = soup.find('title')
                    title = title_tag.get_text().strip() if title_tag else ""
                    
                    # Meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    description = meta_desc.get('content', '') if meta_desc else ""
                    
                    # Main content
                    # Remove script, style, nav, footer
                    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                        tag.decompose()
                    
                    # Get text content
                    content = soup.get_text()
                    
                    # Clean content
                    lines = (line.strip() for line in content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    content = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # Word count kontrolü
                    word_count = len(content.split())
                    if word_count >= 10:  # Minimum word count
                        extracted_data.append({
                            'url': url,
                            'title': title,
                            'description': description,
                            'content': content[:10000],  # Max 10k characters
                            'word_count': word_count,
                            'extracted_at': datetime.now().isoformat(),
                            'content_type': 'text/html'
                        })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Error extracting content from {url}: {str(e)}")
                continue
        
        return extracted_data
    
    def save_to_cloud_storage(self, data: List[Dict], filename: str) -> str:
        """Cloud Storage'a kaydet"""
        try:
            blob_name = f"raw_data/{filename}"
            blob = self.bucket.blob(blob_name)
            
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            blob.upload_from_string(json_data, content_type='application/json')
            
            logger.info(f"Data saved to gs://{BUCKET_NAME}/{blob_name}")
            return f"gs://{BUCKET_NAME}/{blob_name}"
            
        except Exception as e:
            logger.error(f"Error saving to Cloud Storage: {str(e)}")
            raise

@functions_framework.http
def extract_website_data(request):
    """HTTP Cloud Function entry point"""
    
    # CORS headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    headers = {
        'Access-Control-Allow-Origin': '*'
    }
    
    try:
        # Request data'yı al
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return json.dumps({
                'error': 'JSON data required'
            }), 400, headers
        
        url = request_json.get('url')
        max_pages = request_json.get('max_pages', 100)
        
        if not url:
            return json.dumps({
                'error': 'URL required'
            }), 400, headers
        
        logger.info(f"Starting extraction for URL: {url}")
        
        # Extractor'ı başlat
        extractor = CloudWebsiteDataExtractor()
        
        # URL'leri keşfet
        urls = extractor.discover_urls(url, max_pages)
        logger.info(f"Discovered {len(urls)} URLs")
        
        # İçerik çıkar
        data = extractor.extract_content_from_urls(urls)
        logger.info(f"Extracted content from {len(data)} pages")
        
        # Cloud Storage'a kaydet
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"website_data_{timestamp}.json"
        storage_path = extractor.save_to_cloud_storage(data, filename)
        
        # Sonuç
        result = {
            'status': 'success',
            'message': 'Website data extraction completed',
            'stats': {
                'urls_discovered': len(urls),
                'pages_processed': len(data),
                'storage_path': storage_path
            },
            'next_step': 'process-batches',
            'data_file': filename
        }
        
        # PubSub'a mesaj gönder (sonraki step için)
        try:
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
            
            message_data = {
                'step': 'process-batches',
                'data_file': filename,
                'url': url
            }
            
            publisher.publish(topic_path, json.dumps(message_data).encode('utf-8'))
            logger.info("Message sent to PubSub for next step")
            
        except Exception as e:
            logger.warning(f"Failed to send PubSub message: {str(e)}")
        
        return json.dumps(result), 200, headers
        
    except Exception as e:
        logger.error(f"Function error: {str(e)}")
        return json.dumps({
            'error': f'Internal error: {str(e)}'
        }), 500, headers

@functions_framework.cloud_event
def extract_website_data_pubsub(cloud_event):
    """PubSub triggered version"""
    import base64
    
    # Decode PubSub message
    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
    message_json = json.loads(message_data)
    
    url = message_json.get('url')
    max_pages = message_json.get('max_pages', 100)
    
    if not url:
        logger.error("URL not provided in PubSub message")
        return
    
    logger.info(f"Starting PubSub-triggered extraction for URL: {url}")
    
    try:
        extractor = CloudWebsiteDataExtractor()
        urls = extractor.discover_urls(url, max_pages)
        data = extractor.extract_content_from_urls(urls)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"website_data_{timestamp}.json"
        storage_path = extractor.save_to_cloud_storage(data, filename)
        
        logger.info(f"PubSub extraction completed: {storage_path}")
        
        # Trigger next step
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
        
        next_message = {
            'step': 'process-batches',
            'data_file': filename,
            'url': url
        }
        
        publisher.publish(topic_path, json.dumps(next_message).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"PubSub function error: {str(e)}")
        raise 