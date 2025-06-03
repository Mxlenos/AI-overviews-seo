#!/usr/bin/env python3
"""
AI Overview Optimization Projesi - Setup Script
Proje kurulumu ve bağımlılık yönetimi
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Python versiyonunu kontrol et"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 veya üstü gerekli!")
        print(f"Mevcut versiyon: {sys.version}")
        return False
    print(f"✅ Python versiyonu uygun: {sys.version}")
    return True

def check_system_requirements():
    """Sistem gereksinimlerini kontrol et"""
    print("🔍 Sistem gereksinimleri kontrol ediliyor...")
    
    # İşletim sistemi kontrolü
    os_name = platform.system()
    print(f"İşletim sistemi: {os_name}")
    
    # Bellek kontrolü (opsiyonel)
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"Toplam RAM: {memory_gb:.1f} GB")
        
        if memory_gb < 4:
            print("⚠️ En az 4GB RAM önerilir")
        else:
            print("✅ RAM miktarı yeterli")
    except ImportError:
        print("ℹ️ psutil bulunamadı, bellek kontrolü atlandı")
    
    return True

def install_requirements():
    """Requirements.txt'i kur"""
    print("📦 Python paketleri kuruluyor...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt dosyası bulunamadı!")
        return False
    
    try:
        # pip install komutunu çalıştır
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Python paketleri başarıyla kuruldu")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Paket kurulumu başarısız: {e}")
        return False

def setup_directories():
    """Proje dizinlerini oluştur"""
    print("📂 Proje dizinleri oluşturuluyor...")
    
    project_root = Path(__file__).parent
    directories = [
        "data",
        "data/raw",
        "data/processed", 
        "data/batches",
        "logs",
        "config",
        "scripts",
        "tests",
        "tests/data",
        "tests/output",
        "docs"
    ]
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {dir_name}")
    
    return True

def create_env_file():
    """Environment dosyasını oluştur"""
    print("⚙️ Environment dosyası oluşturuluyor...")
    
    env_file = Path(__file__).parent / ".env"
    env_example = Path(__file__).parent / "config" / "env_example.txt"
    
    if env_file.exists():
        print("ℹ️ .env dosyası zaten mevcut")
        return True
    
    if env_example.exists():
        # env_example.txt'i .env olarak kopyala
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ .env dosyası oluşturuldu (env_example.txt'den)")
        print("⚠️ Lütfen .env dosyasını kendi ayarlarınızla güncelleyin!")
    else:
        # Basit .env dosyası oluştur
        with open(env_file, 'w') as f:
            f.write("""# Google Cloud Proje Ayarları
GCP_PROJECT_ID=your-google-cloud-project-id
GCP_REGION=us-central1
GCP_ZONE=us-central1-a

# Google Cloud Kimlik Doğrulama  
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# Vertex AI Search
SEARCH_ENGINE_ID=your-search-engine-id

# Loglama
LOG_LEVEL=INFO

# Web Scraping
USER_AGENT=AI-Overview-Bot/1.0

# Hedef Web Sitesi
TARGET_WEBSITE_URL=https://yourwebsite.com

# AI Overview Tracking
ENABLE_AI_OVERVIEW_TRACKING=true
COSINE_SIMILARITY_THRESHOLD=0.75
""")
        print("✅ .env dosyası oluşturuldu")
        print("⚠️ Lütfen .env dosyasını kendi ayarlarınızla güncelleyin!")
    
    return True

def check_google_cloud_cli():
    """Google Cloud CLI kurulumunu kontrol et"""
    print("☁️ Google Cloud CLI kontrol ediliyor...")
    
    try:
        result = subprocess.run(['gcloud', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Google Cloud CLI kurulu")
            return True
        else:
            print("❌ Google Cloud CLI bulunamadı")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Google Cloud CLI bulunamadı")
        return False

def install_google_cloud_cli():
    """Google Cloud CLI kurulum talimatları"""
    print("\n📋 Google Cloud CLI Kurulum Talimatları:")
    print("=" * 50)
    
    os_name = platform.system()
    
    if os_name == "Windows":
        print("Windows için:")
        print("1. https://cloud.google.com/sdk/docs/install adresini ziyaret edin")
        print("2. GoogleCloudSDKInstaller.exe dosyasını indirin")
        print("3. İndirilen dosyayı çalıştırın ve talimatları takip edin")
        print("4. Kurulumdan sonra terminal'i yeniden başlatın")
        print("5. 'gcloud version' komutuyla kurulumu test edin")
    elif os_name == "Darwin":  # macOS
        print("macOS için:")
        print("1. Homebrew ile: brew install google-cloud-sdk")
        print("2. Veya https://cloud.google.com/sdk/docs/install adresinden manuel kurulum")
    else:  # Linux
        print("Linux için:")
        print("1. sudo apt-get install google-cloud-sdk  (Ubuntu/Debian)")
        print("2. sudo yum install google-cloud-sdk      (RHEL/CentOS)")
        print("3. Veya https://cloud.google.com/sdk/docs/install adresinden manuel kurulum")
    
    print("\nKurulumdan sonra şu komutları çalıştırın:")
    print("gcloud auth login")
    print("gcloud config set project YOUR_PROJECT_ID")

def validate_installation():
    """Kurulumu doğrula"""
    print("\n🔍 Kurulum doğrulanıyor...")
    
    success = True
    
    # Python paketlerini kontrol et
    required_packages = [
        'google-cloud-discoveryengine',
        'google-cloud-storage',
        'pandas',
        'numpy',
        'scikit-learn',
        'sentence-transformers',
        'beautifulsoup4',
        'requests'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} bulunamadı")
            success = False
    
    return success

def main():
    """Ana kurulum fonksiyonu"""
    print("🚀 AI OVERVIEW OPTİMİZASYON PROJESİ KURULUMU")
    print("=" * 60)
    
    # Adım adım kurulum
    steps = [
        ("Python versiyonu kontrolü", check_python_version),
        ("Sistem gereksinimleri kontrolü", check_system_requirements),
        ("Proje dizinleri oluşturma", setup_directories),
        ("Python paketleri kurulumu", install_requirements),
        ("Environment dosyası oluşturma", create_env_file),
        ("Kurulum doğrulama", validate_installation)
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        print(f"\n📋 {step_name}...")
        try:
            if not step_function():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Hata: {e}")
            failed_steps.append(step_name)
    
    # Google Cloud CLI kontrolü (opsiyonel)
    if not check_google_cloud_cli():
        install_google_cloud_cli()
        failed_steps.append("Google Cloud CLI")
    
    # Sonuç
    print("\n" + "=" * 60)
    if not failed_steps:
        print("🎉 KURULUM BAŞARIYLA TAMAMLANDI!")
        print("\n📋 Sonraki Adımlar:")
        print("1. .env dosyasını Google Cloud ayarlarınızla güncelleyin")
        print("2. Google Cloud CLI'ı kurun (eğer kurulu değilse)")
        print("3. gcloud auth login komutunu çalıştırın")
        print("4. Projeyi test edin: python run_project.py --help")
    else:
        print("⚠️ Kurulum tamamlandı ancak bazı sorunlar var:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nLütfen eksik olan bileşenleri manuel olarak kurun.")
    
    print("\n📚 Daha fazla bilgi için README.md dosyasını okuyun.")

if __name__ == "__main__":
    main() 