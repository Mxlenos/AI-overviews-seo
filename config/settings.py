"""
AI Overview Optimization Projesi - Temel Ayarlar
Google Cloud ve Vertex AI konfigürasyon parametreleri
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle (varsa)
load_dotenv()

# Proje Temel Ayarları
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" 
PROCESSED_DATA_DIR = DATA_DIR / "processed"
BATCHES_DIR = DATA_DIR / "batches"
LOGS_DIR = PROJECT_ROOT / "logs"

# Dizinleri oluştur
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, BATCHES_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Google Cloud Ayarları
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'your-project-id')
GCP_REGION = os.getenv('GCP_REGION', 'us-central1')
GCP_ZONE = os.getenv('GCP_ZONE', 'us-central1-a')

# Google Cloud Kimlik Doğrulama
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', None)

# Cloud Storage Ayarları
STORAGE_BUCKET_NAME = f"{GCP_PROJECT_ID}-ai-overview-data"
STORAGE_BATCH_PREFIX = "website-batches"

# Vertex AI Search Ayarları
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID', '')
DISCOVERY_ENGINE_PROJECT = GCP_PROJECT_ID
DISCOVERY_ENGINE_LOCATION = os.getenv('DISCOVERY_ENGINE_LOCATION', 'global')

# Data Store Ayarları  
DATA_STORE_DISPLAY_NAME = "AI Overview Website Data"
DATA_STORE_CONTENT_CONFIG = "CONTENT_REQUIRED"
DATA_STORE_SOLUTION_TYPE = "SOLUTION_TYPE_SEARCH"

# Search Engine Ayarları
SEARCH_ENGINE_DISPLAY_NAME = "AI Overview Search Engine"
SEARCH_ENGINE_SOLUTION_TYPE = "SOLUTION_TYPE_SEARCH"

# Batch İşleme Ayarları
BATCH_SIZE = 50  # Vertex AI'ın önerdiği maksimum URL sayısı
MAX_CONTENT_LENGTH = 10000  # Karakterle maksimum içerik uzunluğu
MIN_CONTENT_LENGTH = 100    # Minimum içerik uzunluğu

# Web Scraping Ayarları
USER_AGENT = os.getenv('USER_AGENT', 'AI-Overview-Bot/1.0')
REQUEST_DELAY = 1.0  # Saniye cinsinden istek arası gecikme
REQUEST_TIMEOUT = 30  # Saniye cinsinden timeout
MAX_RETRIES = 3

# URL Keşif Ayarları
INCLUDE_PATTERNS = [
    r'.*',  # Tüm URL'leri dahil et
]

EXCLUDE_PATTERNS = [
    r'.*\.(pdf|doc|docx|xls|xlsx|ppt|pptx)$',  # Ofis dosyaları
    r'.*\.(jpg|jpeg|png|gif|svg|ico)$',        # Resim dosyaları
    r'.*\.(zip|rar|tar|gz)$',                  # Arşiv dosyaları
    r'.*\.(mp3|mp4|avi|mov|wmv)$',            # Medya dosyaları
    r'.*/admin/.*',                            # Admin sayfaları
    r'.*/wp-admin/.*',                         # WordPress admin
    r'.*/login.*',                             # Login sayfaları
    r'.*/register.*',                          # Kayıt sayfaları
    r'.*\?.*print.*',                          # Print versiyonları
    r'.*#.*',                                  # Anchor linkler
]

# Loglama Ayarları
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# AI Overview Analiz Ayarları
COSINE_SIMILARITY_THRESHOLD = float(os.getenv('COSINE_SIMILARITY_THRESHOLD', '0.75'))
AI_OVERVIEW_SCORE_WEIGHTS = {
    'content_quality': 0.4,
    'keyword_relevance': 0.6
}

# Content Quality Faktörleri
CONTENT_QUALITY_FACTORS = {
    'title_weight': 0.3,
    'content_length_weight': 0.3,
    'relevance_score_weight': 0.4
}

# TF-IDF Ayarları
TFIDF_MAX_FEATURES = 100
TFIDF_STOP_WORDS = 'english'

# Sentence Transformer Ayarları
SENTENCE_TRANSFORMER_MODEL = 'all-MiniLM-L6-v2'

# API Timeout Ayarları
VERTEX_AI_TIMEOUT = 1800  # 30 dakika
CLOUD_STORAGE_TIMEOUT = 600  # 10 dakika
SEARCH_TIMEOUT = 60  # 1 dakika

# Optimizasyon Önerileri Template'leri
OPTIMIZATION_SUGGESTIONS = [
    "H1-H6 başlık yapısını iyileştirin",
    "FAQ bölümleri ekleyin",
    "Listeleme formatını kullanın", 
    "Doğrudan cevap veren paragraflar yazın",
    "İstatistikler ve veri noktaları ekleyin",
    "Schema.org structured data ekleyin",
    "Meta description'ları optimize edin",
    "İç linkleme stratejisini geliştirin",
    "Sayfa yükleme hızını artırın",
    "Mobil uyumluluğu iyileştirin"
]

# Content Analysis Thresholds
AI_OVERVIEW_SCORE_THRESHOLDS = {
    'excellent': 0.8,
    'good': 0.6,
    'average': 0.4,
    'poor': 0.2
}

# File Extensions
SUPPORTED_CONTENT_TYPES = [
    'text/html',
    'application/xhtml+xml',
    'text/plain'
]

# Export Formats
EXPORT_FORMATS = {
    'json': 'application/json',
    'csv': 'text/csv', 
    'txt': 'text/plain',
    'html': 'text/html'
}

# Cloud SQL Ayarları (Opsiyonel)
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = f"{GCP_PROJECT_ID}-ai-overview"
DB_USER = "postgres"
DB_PORT = 5432

# Feature Flags
ENABLE_AI_OVERVIEW_TRACKING = os.getenv('ENABLE_AI_OVERVIEW_TRACKING', 'true').lower() == 'true'
ENABLE_DETAILED_LOGGING = os.getenv('ENABLE_DETAILED_LOGGING', 'false').lower() == 'true'
ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'

# Cache Ayarları
CACHE_TTL = 3600  # 1 saat
CACHE_MAX_SIZE = 1000  # Maksimum cache entry sayısı

# Rate Limiting
RATE_LIMIT_REQUESTS = 100  # 1 dakikada maksimum istek sayısı
RATE_LIMIT_WINDOW = 60     # Saniye cinsinden window

# Debug Ayarları
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
VERBOSE_OUTPUT = os.getenv('VERBOSE_OUTPUT', 'false').lower() == 'true'

# Testing Ayarları
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "data"
TEST_OUTPUT_DIR = PROJECT_ROOT / "tests" / "output"

# Test için dizinleri oluştur
for directory in [TEST_DATA_DIR, TEST_OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Validation Rules
URL_VALIDATION_RULES = {
    'max_url_length': 2048,
    'min_content_words': 10,
    'max_content_words': 10000,
    'required_html_tags': ['title', 'body']
}

# Performance Monitoring
PERFORMANCE_METRICS = {
    'track_extraction_time': True,
    'track_processing_time': True,
    'track_upload_time': True,
    'track_search_time': True
}

# Error Handling
ERROR_HANDLING = {
    'max_consecutive_errors': 10,
    'error_cooldown_seconds': 60,
    'retry_exponential_backoff': True
}

# Notification Settings (Opsiyonel)
NOTIFICATION_SETTINGS = {
    'email_notifications': os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
    'slack_webhook': os.getenv('SLACK_WEBHOOK_URL', ''),
    'discord_webhook': os.getenv('DISCORD_WEBHOOK_URL', '')
}

# Report Generation
REPORT_SETTINGS = {
    'auto_generate_reports': True,
    'report_format': 'both',  # 'json', 'txt', 'both'
    'include_raw_data': False,
    'include_statistics': True
}

# Security Settings
SECURITY_SETTINGS = {
    'validate_ssl': True,
    'follow_redirects': True,
    'max_redirects': 5,
    'respect_robots_txt': True
}

print(f"📋 Ayarlar yüklendi - Proje ID: {GCP_PROJECT_ID}")
if DEBUG_MODE:
    print(f"🐛 Debug modu aktif")
if VERBOSE_OUTPUT:
    print(f"📢 Verbose output aktif") 