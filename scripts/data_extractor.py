"""
Veri Çıkarma Modülü - AI Overview Projesi
Web sitelerinden içerik çıkarır ve yapılandırır.
"""

import os
import sys
import requests
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from tqdm import tqdm

# Proje kök dizinini sys.path'e ekle
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

# Loglama konfigürasyonu
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebsiteDataExtractor:
    """Web sitesi veri çıkarma sınıfı"""
    
    def __init__(self, base_url: str, max_pages: int = 100):
        self.base_url = base_url
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.extracted_data = []
        
    def get_page_content(self, url: str) -> Optional[Dict]:
        """Tek bir sayfadan içerik çıkarır"""
        try:
            time.sleep(REQUEST_DELAY)  # Rate limiting
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Meta bilgileri çıkar
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description.get('content', '') if meta_description else ""
            
            # Ana içeriği çıkar - yaygın HTML etiketlerini kullan
            content_selectors = [
                'article', 'main', '.content', '#content', 
                '.post-content', '.entry-content', '.article-content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    content = content_element.get_text(separator=' ', strip=True)
                    break
            
            # Eğer ana içerik bulunamazsa, body'den çıkar
            if not content:
                body = soup.find('body')
                if body:
                    # Navigasyon, footer gibi öğeleri kaldır
                    for tag in body(['nav', 'footer', 'header', 'aside', 'script', 'style']):
                        tag.decompose()
                    content = body.get_text(separator=' ', strip=True)
            
            # Başlıkları çıkar
            headings = []
            for i in range(1, 7):  # h1-h6
                for heading in soup.find_all(f'h{i}'):
                    headings.append({
                        'level': i,
                        'text': heading.get_text().strip()
                    })
            
            # Bağlantıları çıkar
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') or href.startswith('/'):
                    absolute_url = urljoin(url, href)
                    links.append({
                        'url': absolute_url,
                        'text': link.get_text().strip()
                    })
            
            return {
                'url': url,
                'title': title_text,
                'meta_description': description,
                'content': content,
                'headings': headings,
                'links': links,
                'word_count': len(content.split()),
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Sayfa çıkarma hatası {url}: {str(e)}")
            return None
    
    def discover_pages(self, start_url: str) -> List[str]:
        """Web sitesindeki sayfaları keşfeder"""
        discovered_urls = set()
        to_crawl = [start_url]
        crawled = set()
        
        domain = urlparse(start_url).netloc
        
        while to_crawl and len(discovered_urls) < self.max_pages:
            current_url = to_crawl.pop(0)
            
            if current_url in crawled:
                continue
                
            crawled.add(current_url)
            logger.info(f"Sayfa keşfediliyor: {current_url}")
            
            try:
                response = self.session.get(current_url, timeout=TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                discovered_urls.add(current_url)
                
                # Aynı domain'deki bağlantıları bul
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(current_url, href)
                    parsed_url = urlparse(absolute_url)
                    
                    # Aynı domain ve desteklenen formatlar
                    if (parsed_url.netloc == domain and 
                        absolute_url not in crawled and 
                        absolute_url not in to_crawl and
                        len(discovered_urls) < self.max_pages):
                        
                        # PDF, dosya indirme linklerini filtrele
                        if not any(absolute_url.lower().endswith(ext) 
                                 for ext in ['.pdf', '.doc', '.zip', '.jpg', '.png']):
                            to_crawl.append(absolute_url)
                
                time.sleep(REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Sayfa keşif hatası {current_url}: {str(e)}")
                continue
        
        return list(discovered_urls)
    
    def extract_website_data(self, start_url: str) -> List[Dict]:
        """Tüm web sitesi verilerini çıkarır"""
        logger.info(f"Web sitesi veri çıkarma başlıyor: {start_url}")
        
        # Sayfaları keşfet
        urls = self.discover_pages(start_url)
        logger.info(f"{len(urls)} sayfa keşfedildi")
        
        # Her sayfadan veri çıkar
        extracted_data = []
        for url in tqdm(urls, desc="Sayfalar işleniyor"):
            page_data = self.get_page_content(url)
            if page_data:
                extracted_data.append(page_data)
        
        logger.info(f"{len(extracted_data)} sayfa başarıyla işlendi")
        return extracted_data
    
    def save_raw_data(self, data: List[Dict], filename: str = None):
        """Ham veriyi dosyaya kaydet"""
        if not filename:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"raw_website_data_{timestamp}.json"
        
        filepath = RAW_DATA_DIR / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Ham veri kaydedildi: {filepath}")
        return filepath

def main():
    """Ana fonksiyon - komut satırından çalıştırma"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web sitesi veri çıkarma')
    parser.add_argument('--url', required=True, help='Hedef web sitesi URL')
    parser.add_argument('--max-pages', type=int, default=100, help='Maksimum sayfa sayısı')
    parser.add_argument('--output', help='Çıktı dosya adı')
    
    args = parser.parse_args()
    
    # Veri çıkarma
    extractor = WebsiteDataExtractor(args.url, args.max_pages)
    data = extractor.extract_website_data(args.url)
    
    # Kaydetme
    output_file = extractor.save_raw_data(data, args.output)
    
    print(f"\n✅ Veri çıkarma tamamlandı!")
    print(f"📊 İşlenen sayfa sayısı: {len(data)}")
    print(f"💾 Çıktı dosyası: {output_file}")
    
    # Özet istatistikler
    total_words = sum(item['word_count'] for item in data)
    print(f"📝 Toplam kelime sayısı: {total_words:,}")
    print(f"📄 Ortalama sayfa uzunluğu: {total_words // len(data) if data else 0} kelime")

if __name__ == "__main__":
    main() 