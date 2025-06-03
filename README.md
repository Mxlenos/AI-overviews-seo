# AI Overview Optimization Projesi

Bu proje, Google Cloud'un Vertex AI Search Agent ve Discovery Engine kullanarak web sitenizi AI Overviews için optimize etmeyi amaçlamaktadır.

## 🎯 Proje Amacı

- Web siteniz için izole bir arama indeksi oluşturma
- Site-özel arama motoru kurma
- AI destekli arama sonuçları için içerik optimizasyonu
- Google AI Overview'larda görünürlük artırma

## 📋 Kurulum Adımları

### 1. Google Cloud CLI Kurulumu
```bash
# Windows için
# Google Cloud CLI'ı şu linkten indirin: https://cloud.google.com/sdk/docs/install
```

### 2. Python Sanal Ortamı
```bash
python -m venv ai_overview_env
ai_overview_env\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Google Cloud Kimlik Doğrulama
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## 🏗️ Proje Yapısı

```
ai_overview_project/
├── config/
│   ├── settings.py
│   └── gcp_config.json
├── data/
│   ├── raw/
│   ├── processed/
│   └── batches/
├── scripts/
│   ├── data_extractor.py
│   ├── batch_processor.py
│   ├── vertex_ai_setup.py
│   └── search_engine_builder.py
├── tests/
└── docs/
```

## 🚀 Kullanım

1. **Veri Çıkarma**: Web sitenizden içerikleri çıkarın
2. **Batch İşleme**: İçerikleri 50'şer URL'lik parçalara bölün
3. **Cloud Storage**: Verileri Google Cloud Storage'a yükleyin
4. **Vertex AI Kurulumu**: Arama indekslerini oluşturun
5. **Optimizasyon**: AI Overview için içerikleri optimize edin

## 📊 Özellikler

- ✅ Otomatik web scraping
- ✅ Batch processing
- ✅ Cloud Storage entegrasyonu
- ✅ Vertex AI Search konfigürasyonu
- ✅ AI Overview tracking
- ✅ Performance monitoring

## 📝 Notlar

- Google Cloud hesabınızın billing aktif olması gerekir
- Vertex AI API'lerinin etkinleştirilmiş olması gerekir
- Proje maliyetlerini takip etmeyi unutmayın 