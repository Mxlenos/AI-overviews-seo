"""
Batch İşleme Modülü - AI Overview Projesi
Ham web sitesi verilerini 50'şer URL'lik batch'lere böler ve işler.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict
import logging
from math import ceil

# Proje kök dizinini sys.path'e ekle
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

# Loglama konfigürasyonu
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchProcessor:
    """Veri batch işleme sınıfı"""
    
    def __init__(self):
        self.batches = []
        self.metadata = {}
        
    def load_raw_data(self, raw_data_file: Path) -> List[Dict]:
        """Ham veri dosyasını yükler"""
        logger.info(f"Ham veri yükleniyor: {raw_data_file}")
        
        with open(raw_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"{len(data)} kayıt yüklendi")
        return data
    
    def clean_and_validate_data(self, data: List[Dict]) -> List[Dict]:
        """Veriyi temizler ve doğrular"""
        cleaned_data = []
        
        for item in data:
            # Temel alanları kontrol et
            if not item.get('url') or not item.get('content'):
                logger.warning(f"Eksik veri atlanıyor: {item.get('url', 'URL yok')}")
                continue
            
            # İçerik uzunluğu kontrolü
            word_count = len(item['content'].split())
            if word_count < CONTENT_OPTIMIZATION_RULES['min_word_count']:
                logger.warning(f"Çok kısa içerik atlanıyor: {item['url']} ({word_count} kelime)")
                continue
            
            # Çok uzun içerikleri kısalt
            if word_count > CONTENT_OPTIMIZATION_RULES['max_word_count']:
                words = item['content'].split()[:CONTENT_OPTIMIZATION_RULES['max_word_count']]
                item['content'] = ' '.join(words)
                item['word_count'] = len(words)
                logger.info(f"İçerik kısaltıldı: {item['url']} ({word_count} -> {len(words)} kelime)")
            
            # Başlık kontrolü
            if not item.get('title'):
                item['title'] = f"Sayfa - {item['url'].split('/')[-1]}"
            
            # Meta açıklama kontrolü
            if not item.get('meta_description'):
                # İçeriğin ilk 160 karakterini kullan
                item['meta_description'] = item['content'][:160] + "..." if len(item['content']) > 160 else item['content']
            
            cleaned_data.append(item)
        
        logger.info(f"Veri temizleme tamamlandı: {len(data)} -> {len(cleaned_data)} kayıt")
        return cleaned_data
    
    def create_batches(self, data: List[Dict]) -> List[List[Dict]]:
        """Veriyi batch'lere böler"""
        batches = []
        total_batches = ceil(len(data) / MAX_URLS_PER_BATCH)
        
        logger.info(f"Veri {total_batches} batch'e bölünüyor (her batch'te {MAX_URLS_PER_BATCH} URL)")
        
        for i in range(0, len(data), MAX_URLS_PER_BATCH):
            batch = data[i:i + MAX_URLS_PER_BATCH]
            batches.append(batch)
        
        return batches
    
    def optimize_content_for_ai(self, content: str, title: str = "") -> str:
        """İçeriği AI Overview için optimize eder"""
        # Başlık varsa içeriğe ekle
        if title:
            optimized_content = f"# {title}\n\n{content}"
        else:
            optimized_content = content
        
        # Paragrafları ayır ve temizle
        paragraphs = [p.strip() for p in optimized_content.split('\n') if p.strip()]
        
        # Çok kısa paragrafları birleştir
        merged_paragraphs = []
        current_paragraph = ""
        
        for paragraph in paragraphs:
            if len(paragraph.split()) < 20 and current_paragraph:
                current_paragraph += " " + paragraph
            else:
                if current_paragraph:
                    merged_paragraphs.append(current_paragraph)
                current_paragraph = paragraph
        
        if current_paragraph:
            merged_paragraphs.append(current_paragraph)
        
        return '\n\n'.join(merged_paragraphs)
    
    def create_batch_metadata(self, batch_id: str, batch_data: List[Dict]) -> Dict:
        """Batch metadata'sını oluşturur"""
        urls = [item['url'] for item in batch_data]
        total_words = sum(item['word_count'] for item in batch_data)
        
        metadata = {
            'batch_id': batch_id,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'url_count': len(batch_data),
            'urls': urls,
            'total_words': total_words,
            'average_words_per_page': total_words // len(batch_data) if batch_data else 0,
            'file_format': BATCH_FILE_FORMAT,
            'processing_status': 'created'
        }
        
        return metadata
    
    def save_batch_as_jsonl(self, batch_data: List[Dict], batch_id: str) -> Path:
        """Batch'i JSONL formatında kaydeder"""
        filename = f"batch_{batch_id}.{BATCH_FILE_FORMAT}"
        filepath = BATCHES_DIR / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in batch_data:
                # AI Overview için optimize et
                optimized_item = item.copy()
                optimized_item['content'] = self.optimize_content_for_ai(
                    item['content'], 
                    item.get('title', '')
                )
                
                # JSONL formatında yaz (her satırda bir JSON)
                json.dump(optimized_item, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Batch kaydedildi: {filepath}")
        return filepath
    
    def save_metadata(self, all_metadata: List[Dict]) -> Path:
        """Tüm batch metadata'larını kaydeder"""
        metadata_file = BATCHES_DIR / "batches_metadata.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Metadata kaydedildi: {metadata_file}")
        return metadata_file
    
    def process_data_to_batches(self, raw_data_file: Path) -> Dict:
        """Ana işleme fonksiyonu"""
        logger.info("Batch işleme başlıyor...")
        
        # Ham veriyi yükle
        raw_data = self.load_raw_data(raw_data_file)
        
        # Veriyi temizle ve doğrula
        cleaned_data = self.clean_and_validate_data(raw_data)
        
        if not cleaned_data:
            raise ValueError("İşlenecek geçerli veri bulunamadı")
        
        # Batch'lere böl
        batches = self.create_batches(cleaned_data)
        
        # Her batch'i işle ve kaydet
        batch_files = []
        all_metadata = []
        
        for i, batch_data in enumerate(batches, 1):
            batch_id = f"{int(time.time())}_{i:03d}"
            
            # Batch dosyasını kaydet
            batch_file = self.save_batch_as_jsonl(batch_data, batch_id)
            batch_files.append(batch_file)
            
            # Metadata oluştur
            metadata = self.create_batch_metadata(batch_id, batch_data)
            all_metadata.append(metadata)
            
            logger.info(f"Batch {i}/{len(batches)} işlendi: {len(batch_data)} URL")
        
        # Metadata'yı kaydet
        metadata_file = self.save_metadata(all_metadata)
        
        # Özet rapor
        summary = {
            'total_pages_processed': len(cleaned_data),
            'total_batches_created': len(batches),
            'batch_files': [str(f) for f in batch_files],
            'metadata_file': str(metadata_file),
            'processing_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'average_pages_per_batch': len(cleaned_data) / len(batches) if batches else 0
        }
        
        logger.info("Batch işleme tamamlandı!")
        return summary

def main():
    """Ana fonksiyon - komut satırından çalıştırma"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Veri batch işleme')
    parser.add_argument('--input', required=True, help='Ham veri dosyası yolu')
    parser.add_argument('--output-dir', help='Çıktı dizini (varsayılan: data/batches)')
    
    args = parser.parse_args()
    
    # Dosya kontrolü
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ Hata: Dosya bulunamadı: {input_file}")
        return
    
    # Çıktı dizini ayarla
    if args.output_dir:
        global BATCHES_DIR
        BATCHES_DIR = Path(args.output_dir)
    
    # Batch işleme
    processor = BatchProcessor()
    try:
        summary = processor.process_data_to_batches(input_file)
        
        print(f"\n✅ Batch işleme tamamlandı!")
        print(f"📊 İşlenen sayfa sayısı: {summary['total_pages_processed']}")
        print(f"📦 Oluşturulan batch sayısı: {summary['total_batches_created']}")
        print(f"📄 Ortalama batch büyüklüğü: {summary['average_pages_per_batch']:.1f} sayfa")
        print(f"📁 Batch dosyaları: {BATCHES_DIR}")
        print(f"📋 Metadata dosyası: {summary['metadata_file']}")
        
    except Exception as e:
        logger.error(f"Batch işleme hatası: {str(e)}")
        print(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    main() 