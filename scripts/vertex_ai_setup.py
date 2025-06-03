"""
Vertex AI Search Kurulum Modülü - AI Overview Projesi
Google Cloud Vertex AI Search ve Discovery Engine kurulumu yapır.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Google Cloud kütüphaneleri
try:
    from google.cloud import storage
    from google.cloud import discoveryengine
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
except ImportError as e:
    print("❌ Google Cloud kütüphaneleri bulunamadı. Lütfen requirements.txt'i yükleyin:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Proje kök dizinini sys.path'e ekle
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

# Loglama konfigürasyonu
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VertexAISetup:
    """Vertex AI Search kurulum sınıfı"""
    
    def __init__(self):
        self.project_id = GCP_PROJECT_ID
        self.location = DISCOVERY_ENGINE_LOCATION
        self.storage_client = None
        self.discovery_client = None
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Google Cloud client'larını başlat"""
        try:
            # Kimlik doğrulama kontrolü
            credentials, project = default()
            logger.info(f"Google Cloud kimlik doğrulaması başarılı: {project}")
            
            # Client'ları başlat
            self.storage_client = storage.Client(project=self.project_id)
            self.discovery_client = discoveryengine.DataStoreServiceClient()
            
            logger.info("Google Cloud client'ları başlatıldı")
            
        except DefaultCredentialsError:
            logger.error("Google Cloud kimlik doğrulaması başarısız!")
            print("❌ Google Cloud kimlik doğrulaması gerekli. Lütfen şu adımları takip edin:")
            print("1. gcloud auth login")
            print("2. gcloud config set project YOUR_PROJECT_ID")
            print("3. Service account key dosyası ayarlayın")
            raise
        except Exception as e:
            logger.error(f"Client başlatma hatası: {str(e)}")
            raise
    
    def check_project_setup(self) -> bool:
        """Proje kurulumunu kontrol eder"""
        logger.info(f"Proje kurulumu kontrol ediliyor: {self.project_id}")
        
        try:
            # Projede gerekli API'lerin etkin olup olmadığını kontrol et
            required_apis = [
                'discoveryengine.googleapis.com',
                'storage.googleapis.com',
                'compute.googleapis.com'
            ]
            
            logger.info("Gerekli API'ler kontrol ediliyor...")
            
            # Storage client ile temel bağlantıyı test et
            try:
                list(self.storage_client.list_buckets(max_results=1))
                logger.info("✅ Cloud Storage API aktif")
            except Exception as e:
                logger.error(f"❌ Cloud Storage API sorunu: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Proje kurulum kontrolü başarısız: {str(e)}")
            return False
    
    def create_storage_bucket(self) -> bool:
        """Cloud Storage bucket oluşturur"""
        bucket_name = STORAGE_BUCKET_NAME
        logger.info(f"Storage bucket oluşturuluyor: {bucket_name}")
        
        try:
            # Bucket'ın zaten var olup olmadığını kontrol et
            try:
                bucket = self.storage_client.bucket(bucket_name)
                bucket.reload()
                logger.info(f"✅ Bucket zaten mevcut: {bucket_name}")
                return True
            except Exception:
                pass  # Bucket mevcut değil, oluşturacağız
            
            # Yeni bucket oluştur
            bucket = self.storage_client.bucket(bucket_name)
            bucket = self.storage_client.create_bucket(
                bucket, 
                location=GCP_REGION
            )
            
            logger.info(f"✅ Storage bucket oluşturuldu: {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Bucket oluşturma hatası: {str(e)}")
            return False
    
    def upload_batch_to_storage(self, batch_file: Path) -> Optional[str]:
        """Batch dosyasını Cloud Storage'a yükler"""
        bucket_name = STORAGE_BUCKET_NAME
        blob_name = f"{STORAGE_BATCH_PREFIX}/{batch_file.name}"
        
        logger.info(f"Dosya Cloud Storage'a yükleniyor: {batch_file.name}")
        
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.upload_from_filename(str(batch_file))
            
            # Public URL oluştur
            public_url = f"gs://{bucket_name}/{blob_name}"
            logger.info(f"✅ Dosya yüklendi: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"❌ Dosya yükleme hatası: {str(e)}")
            return None
    
    def create_data_store(self, data_store_id: str, display_name: str) -> bool:
        """Discovery Engine data store oluşturur"""
        logger.info(f"Data store oluşturuluyor: {data_store_id}")
        
        try:
            # Data store konfigürasyonu
            data_store = discoveryengine.DataStore(
                display_name=display_name,
                industry_vertical=discoveryengine.IndustryVertical.GENERIC,
                solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
                content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
            )
            
            # Parent path oluştur
            parent = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection"
            
            # Data store oluşturma isteği
            request = discoveryengine.CreateDataStoreRequest(
                parent=parent,
                data_store=data_store,
                data_store_id=data_store_id,
            )
            
            # İşlemi başlat
            operation = self.discovery_client.create_data_store(request=request)
            logger.info("Data store oluşturma işlemi başlatıldı...")
            
            # İşlemin tamamlanmasını bekle
            response = operation.result(timeout=300)  # 5 dakika timeout
            
            logger.info(f"✅ Data store oluşturuldu: {response.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data store oluşturma hatası: {str(e)}")
            return False
    
    def create_search_engine(self, engine_id: str, display_name: str, data_store_ids: List[str]) -> bool:
        """Search engine oluşturur"""
        logger.info(f"Search engine oluşturuluyor: {engine_id}")
        
        try:
            # Engine client
            engine_client = discoveryengine.EngineServiceClient()
            
            # Data store referansları
            data_store_specs = []
            for data_store_id in data_store_ids:
                data_store_spec = discoveryengine.Engine.SearchEngineConfig.DataStoreSpec(
                    data_store=f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/dataStores/{data_store_id}"
                )
                data_store_specs.append(data_store_spec)
            
            # Search engine konfigürasyonu
            search_engine_config = discoveryengine.Engine.SearchEngineConfig(
                search_tier=discoveryengine.SearchTier.SEARCH_TIER_STANDARD,
                search_add_ons=[discoveryengine.SearchAddOn.SEARCH_ADD_ON_LLM],
                data_store_specs=data_store_specs,
            )
            
            engine = discoveryengine.Engine(
                display_name=display_name,
                solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
                industry_vertical=discoveryengine.IndustryVertical.GENERIC,
                search_engine_config=search_engine_config,
            )
            
            # Parent path
            parent = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection"
            
            # Request
            request = discoveryengine.CreateEngineRequest(
                parent=parent,
                engine=engine,
                engine_id=engine_id,
            )
            
            # İşlemi başlat
            operation = engine_client.create_engine(request=request)
            logger.info("Search engine oluşturma işlemi başlatıldı...")
            
            # İşlemin tamamlanmasını bekle
            response = operation.result(timeout=600)  # 10 dakika timeout
            
            logger.info(f"✅ Search engine oluşturuldu: {response.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Search engine oluşturma hatası: {str(e)}")
            return False
    
    def setup_complete_pipeline(self, website_name: str) -> Dict:
        """Komple AI Overview pipeline'ı kurar"""
        logger.info("AI Overview pipeline kurulumu başlıyor...")
        
        setup_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'project_id': self.project_id,
            'website_name': website_name,
            'steps': {},
            'success': False
        }
        
        try:
            # 1. Proje kurulumu kontrolü
            logger.info("1️⃣ Proje kurulumu kontrol ediliyor...")
            if not self.check_project_setup():
                setup_results['steps']['project_check'] = False
                return setup_results
            setup_results['steps']['project_check'] = True
            
            # 2. Storage bucket oluştur
            logger.info("2️⃣ Storage bucket oluşturuluyor...")
            if not self.create_storage_bucket():
                setup_results['steps']['storage_bucket'] = False
                return setup_results
            setup_results['steps']['storage_bucket'] = True
            
            # 3. Data store oluştur
            data_store_id = f"{website_name.lower().replace(' ', '-')}-data-store"
            logger.info("3️⃣ Data store oluşturuluyor...")
            if not self.create_data_store(data_store_id, f"{website_name} Data Store"):
                setup_results['steps']['data_store'] = False
                return setup_results
            setup_results['steps']['data_store'] = True
            setup_results['data_store_id'] = data_store_id
            
            # 4. Search engine oluştur
            engine_id = f"{website_name.lower().replace(' ', '-')}-search-engine"
            logger.info("4️⃣ Search engine oluşturuluyor...")
            if not self.create_search_engine(engine_id, f"{website_name} Search Engine", [data_store_id]):
                setup_results['steps']['search_engine'] = False
                return setup_results
            setup_results['steps']['search_engine'] = True
            setup_results['search_engine_id'] = engine_id
            
            setup_results['success'] = True
            logger.info("✅ AI Overview pipeline kurulumu tamamlandı!")
            
        except Exception as e:
            logger.error(f"❌ Pipeline kurulum hatası: {str(e)}")
            setup_results['error'] = str(e)
        
        return setup_results

def main():
    """Ana fonksiyon - komut satırından çalıştırma"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vertex AI Search kurulumu')
    parser.add_argument('--website-name', required=True, help='Web sitesi adı')
    parser.add_argument('--project-id', help='Google Cloud Project ID')
    
    args = parser.parse_args()
    
    # Project ID'yi güncelle
    if args.project_id:
        global GCP_PROJECT_ID
        GCP_PROJECT_ID = args.project_id
    
    # Kurulum başlat
    setup = VertexAISetup()
    results = setup.setup_complete_pipeline(args.website_name)
    
    # Sonuçları göster
    print(f"\n🚀 Vertex AI Search Kurulum Raporu")
    print(f"{'='*50}")
    print(f"📅 Tarih: {results['timestamp']}")
    print(f"🌐 Web Sitesi: {results['website_name']}")
    print(f"🏗️ Proje ID: {results['project_id']}")
    print(f"\n📋 Kurulum Adımları:")
    
    for step, success in results['steps'].items():
        status = "✅" if success else "❌"
        print(f"  {status} {step.replace('_', ' ').title()}")
    
    if results['success']:
        print(f"\n🎉 Kurulum başarıyla tamamlandı!")
        print(f"🔍 Data Store ID: {results.get('data_store_id')}")
        print(f"🔧 Search Engine ID: {results.get('search_engine_id')}")
        print(f"\n📝 Bir sonraki adımlar:")
        print(f"  1. Batch dosyalarınızı data store'a yükleyin")
        print(f"  2. Search engine'i test edin")
        print(f"  3. AI Overview optimizasyonunu başlatın")
    else:
        print(f"\n❌ Kurulum başarısız!")
        if 'error' in results:
            print(f"🔍 Hata: {results['error']}")

if __name__ == "__main__":
    main() 