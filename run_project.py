#!/usr/bin/env python3
"""
AI Overview Projesi - Ana Çalıştırma Scripti
Proje süreçlerini yönetir ve koordine eder.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional

# Proje kök dizinini sys.path'e ekle
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Proje modüllerini import et
try:
    from scripts.data_extractor import WebsiteDataExtractor
    from scripts.batch_processor import BatchProcessor
    from scripts.vertex_ai_setup import VertexAISetup
    from scripts.search_engine_builder import SearchEngineBuilder
    from config.settings import *
except ImportError as e:
    print(f"❌ Proje modülleri yüklenemedi: {e}")
    print("Lütfen requirements.txt'i yüklediğinizden emin olun:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Loglama konfigürasyonu
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def step_1_extract_website_data(url: str, max_pages: int = 100) -> bool:
    """Adım 1: Web sitesinden veri çıkarma"""
    print("🚀 ADIM 1: Web Sitesi Veri Çıkarma")
    print(f"Hedef URL: {url}")
    print(f"Maksimum sayfa: {max_pages}")
    print("-" * 50)
    
    try:
        extractor = WebsiteDataExtractor(url, max_pages)
        
        # Sitemap analizi
        print("📋 Sitemap analizi yapılıyor...")
        urls = extractor.discover_urls()
        print(f"✅ {len(urls)} URL keşfedildi")
        
        # İçerik çıkarma
        print("📄 İçerik çıkarılıyor...")
        data = extractor.extract_content_from_urls(urls)
        
        # Verileri kaydet
        output_file = extractor.save_extracted_data(data)
        print(f"✅ Veriler kaydedildi: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Veri çıkarma hatası: {str(e)}")
        print(f"❌ Hata: {str(e)}")
        return False

def step_2_process_batches(raw_data_file: Path) -> List[Path]:
    """Adım 2: Verileri batch'lere böl"""
    print("\n🔄 ADIM 2: Batch İşleme")
    print(f"Ham veri dosyası: {raw_data_file}")
    print("-" * 50)
    
    try:
        processor = BatchProcessor()
        
        # Ham verileri yükle
        print("📂 Ham veriler yükleniyor...")
        raw_data = processor.load_raw_data(raw_data_file)
        print(f"✅ {len(raw_data)} kayıt yüklendi")
        
        # Batch'lere böl
        print("✂️ Batch'lere bölünüyor...")
        batch_files = processor.create_batches(raw_data)
        print(f"✅ {len(batch_files)} batch oluşturuldu")
        
        return batch_files
        
    except Exception as e:
        logger.error(f"Batch işleme hatası: {str(e)}")
        print(f"❌ Hata: {str(e)}")
        return []

def step_3_setup_vertex_ai(batch_files: List[Path]) -> Dict[str, str]:
    """Adım 3: Vertex AI kurulumu"""
    print("\n☁️ ADIM 3: Vertex AI Kurulumu")
    print(f"{len(batch_files)} batch dosyası işlenecek")
    print("-" * 50)
    
    try:
        vertex_setup = VertexAISetup()
        
        # Cloud Storage bucket oluştur
        print("🗂️ Cloud Storage bucket oluşturuluyor...")
        bucket_created = vertex_setup.create_storage_bucket()
        if bucket_created:
            print("✅ Bucket oluşturuldu")
        
        # Batch dosyalarını Cloud Storage'a yükle
        print("⬆️ Batch dosyaları yükleniyor...")
        upload_success = vertex_setup.upload_batch_files(batch_files)
        if not upload_success:
            print("❌ Dosya yükleme başarısız!")
            return {}
        
        # Data store oluştur
        print("📊 Data store oluşturuluyor...")
        data_store_id = vertex_setup.create_data_store()
        if not data_store_id:
            print("❌ Data store oluşturulamadı!")
            return {}
        
        # Search engine oluştur
        print("🔍 Search engine oluşturuluyor...")
        engine_id = vertex_setup.create_search_engine(data_store_id)
        if not engine_id:
            print("❌ Search engine oluşturulamadı!")
            return {}
        
        print("✅ Vertex AI kurulumu tamamlandı!")
        
        return {
            'data_store_id': data_store_id,
            'engine_id': engine_id
        }
        
    except Exception as e:
        logger.error(f"Vertex AI kurulum hatası: {str(e)}")
        print(f"❌ Hata: {str(e)}")
        return {}

def step_4_import_and_analyze(engine_id: str, data_store_id: str, batch_files: List[Path], 
                             query: str, keywords: List[str]) -> bool:
    """Adım 4: Import ve AI Overview analizi"""
    print("\n🤖 ADIM 4: Import ve AI Overview Analizi")
    print(f"Search Engine ID: {engine_id}")
    print(f"Data Store ID: {data_store_id}")
    print(f"Arama sorgusu: {query}")
    print(f"Hedef kelimeler: {', '.join(keywords)}")
    print("-" * 50)
    
    try:
        builder = SearchEngineBuilder()
        
        # Dokümanları import et
        print("📥 Dokümanlar import ediliyor...")
        import_success = builder.import_documents_to_datastore(data_store_id, batch_files)
        if not import_success:
            print("❌ Import başarısız!")
            return False
        
        print("⏳ Import işleminin tamamlanması bekleniyor (5 dakika)...")
        import time
        time.sleep(300)  # 5 dakika bekle
        
        # Arama testi
        print("🔍 Arama testi yapılıyor...")
        search_results = builder.search_documents(engine_id, query)
        
        if not search_results.get('results'):
            print("⚠️ Henüz arama sonucu yok, daha fazla bekleme gerekebilir")
            print("Import işleminin tamamlanması 30 dakika kadar sürebilir")
            return True
        
        # AI Overview analizi
        print("🧠 AI Overview analizi yapılıyor...")
        analysis = builder.analyze_ai_overview_potential(search_results, keywords)
        
        # Sonuçları kaydet
        result_file = builder.save_analysis_results(analysis, search_results)
        
        # Özet rapor
        print("\n📊 ANALIZ SONUÇLARI")
        print("=" * 50)
        print(f"AI Overview Skoru: {analysis.get('ai_overview_score', 0):.1%}")
        print(f"İçerik Kalitesi: {analysis.get('content_quality_score', 0):.1%}")
        print(f"Anahtar Kelime Uyumu: {analysis.get('keyword_relevance_score', 0):.1%}")
        print(f"Bulunan Doküman: {len(search_results.get('results', []))}")
        
        print("\n💡 ÖNERİLER:")
        recommendations = analysis.get('recommendations', [])
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec}")
        
        print(f"\n📁 Detaylı rapor: {result_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Import ve analiz hatası: {str(e)}")
        print(f"❌ Hata: {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description='AI Overview Optimization Projesi')
    parser.add_argument('--url', required=True, help='Hedef web sitesi URL\'i')
    parser.add_argument('--query', required=True, help='Test arama sorgusu')
    parser.add_argument('--keywords', nargs='+', required=True, help='Hedef anahtar kelimeler')
    parser.add_argument('--max-pages', type=int, default=100, help='Maksimum sayfa sayısı (varsayılan: 100)')
    parser.add_argument('--skip-extract', action='store_true', help='Veri çıkarmayı atla')
    parser.add_argument('--skip-vertex', action='store_true', help='Vertex AI kurulumunu atla')
    parser.add_argument('--raw-data-file', help='Mevcut ham veri dosyası (veri çıkarma atlanırsa)')
    parser.add_argument('--engine-id', help='Mevcut search engine ID (Vertex AI kurulumu atlanırsa)')
    parser.add_argument('--data-store-id', help='Mevcut data store ID (Vertex AI kurulumu atlanırsa)')
    
    args = parser.parse_args()
    
    print("🎯 AI OVERVIEW OPTİMİZASYON PROJESİ")
    print("=" * 60)
    print(f"Hedef URL: {args.url}")
    print(f"Arama sorgusu: {args.query}")
    print(f"Hedef kelimeler: {', '.join(args.keywords)}")
    print(f"Maksimum sayfa: {args.max_pages}")
    print("=" * 60)
    
    try:
        # Adım 1: Veri çıkarma
        raw_data_file = None
        if not args.skip_extract:
            success = step_1_extract_website_data(args.url, args.max_pages)
            if not success:
                print("❌ Proje durduruldu: Veri çıkarma başarısız")
                return
            
            # En son oluşturulan ham veri dosyasını bul
            raw_data_files = list(RAW_DATA_DIR.glob("website_data_*.json"))
            if raw_data_files:
                raw_data_file = max(raw_data_files, key=lambda f: f.stat().st_mtime)
        else:
            if args.raw_data_file:
                raw_data_file = Path(args.raw_data_file)
                if not raw_data_file.exists():
                    print(f"❌ Ham veri dosyası bulunamadı: {raw_data_file}")
                    return
            else:
                # En son oluşturulan dosyayı bul
                raw_data_files = list(RAW_DATA_DIR.glob("website_data_*.json"))
                if raw_data_files:
                    raw_data_file = max(raw_data_files, key=lambda f: f.stat().st_mtime)
                else:
                    print("❌ Ham veri dosyası bulunamadı. --raw-data-file parametresini kullanın.")
                    return
        
        # Adım 2: Batch işleme
        batch_files = step_2_process_batches(raw_data_file)
        if not batch_files:
            print("❌ Proje durduruldu: Batch işleme başarısız")
            return
        
        # Adım 3: Vertex AI kurulumu
        engine_id = args.engine_id
        data_store_id = args.data_store_id
        
        if not args.skip_vertex:
            vertex_result = step_3_setup_vertex_ai(batch_files)
            if not vertex_result:
                print("❌ Proje durduruldu: Vertex AI kurulumu başarısız")
                return
            
            engine_id = vertex_result['engine_id']
            data_store_id = vertex_result['data_store_id']
        else:
            if not engine_id or not data_store_id:
                print("❌ --engine-id ve --data-store-id parametreleri gerekli (Vertex AI kurulumu atlandığında)")
                return
        
        # Adım 4: Import ve analiz
        success = step_4_import_and_analyze(
            engine_id, data_store_id, batch_files, 
            args.query, args.keywords
        )
        
        if success:
            print("\n🎉 PROJE BAŞARIYLA TAMAMLANDI!")
            print("=" * 50)
            print(f"Search Engine ID: {engine_id}")
            print(f"Data Store ID: {data_store_id}")
            print("Google Cloud Console'dan ilerleyişi takip edebilirsiniz.")
        else:
            print("\n❌ Proje tamamlanamadı!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Proje kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        print(f"\n❌ Beklenmeyen hata: {str(e)}")

if __name__ == "__main__":
    main() 