# 🚀 AI Overview Optimization - Hızlı Başlangıç

## ⚡ 5 Dakikada Çalışan Sistem!

### 1️⃣ API'leri Etkinleştir (2 dakika)
https://console.cloud.google.com/apis/library

Bu API'leri arayıp **ENABLE** et:
- Cloud Functions API
- Cloud Run API
- Cloud Storage API
- Pub/Sub API
- Discovery Engine API
- Cloud Build API

### 2️⃣ Storage Bucket Oluştur (1 dakika)
https://console.cloud.google.com/storage

**CREATE BUCKET:**
- Name: `ai-overviews-v1-ai-overview-data`
- Region: `us-central1`
- Standard storage class

### 3️⃣ Cloud Functions Deploy Et (1 dakika)

#### Extract Function:
1. https://console.cloud.google.com/functions
2. **CREATE FUNCTION**
3. Name: `extract-website-data`
4. Region: `us-central1`
5. HTTP Trigger, Allow unauthenticated
6. Python 3.11, Entry point: `extract_website_data`
7. Kodu `functions/extract_website_data/` klasöründen kopyala
8. Environment variables:
   ```
   GCP_PROJECT_ID = ai-overviews-v1
   STORAGE_BUCKET_NAME = ai-overviews-v1-ai-overview-data
   PUBSUB_TOPIC = ai-overview-pipeline
   ```

#### Process Function:
- Name: `process-batches`
- Entry point: `process_batches`
- Code: `functions/process_batches/`

#### Vertex AI Function:
- Name: `setup-vertex-ai`
- Entry point: `setup_vertex_ai`
- Memory: 1GB, Timeout: 540s
- Code: `functions/setup_vertex_ai/`

### 4️⃣ Cloud Run Deploy Et (1 dakika)
1. https://console.cloud.google.com/run
2. **CREATE SERVICE**
3. Name: `ai-overview-web-app`
4. Source: Upload ZIP (`web_app/` klasörü)
5. Port: 8080
6. Environment variables:
   ```
   GCP_PROJECT_ID = ai-overviews-v1
   STORAGE_BUCKET_NAME = ai-overviews-v1-ai-overview-data
   PUBSUB_TOPIC = ai-overview-pipeline
   EXTRACT_FUNCTION_URL = https://us-central1-ai-overviews-v1.cloudfunctions.net/extract-website-data
   ```

### 5️⃣ PubSub Topic Oluştur (30 saniye)
1. https://console.cloud.google.com/cloudpubsub
2. **CREATE TOPIC**
3. Topic ID: `ai-overview-pipeline`

### ✅ Test Et!
Web app URL'ine git ve ilk analizi başlat!

---

## 🔗 Yararlı Linkler

- **Console:** https://console.cloud.google.com
- **Functions:** https://console.cloud.google.com/functions
- **Cloud Run:** https://console.cloud.google.com/run
- **Storage:** https://console.cloud.google.com/storage
- **Pub/Sub:** https://console.cloud.google.com/cloudpubsub

## 🆘 Sorun mu var?

1. **API'ler enabled mi?** - APIs & Services > Dashboard kontrol et
2. **Billing aktif mi?** - Billing kontrol et
3. **Permissions yeterli mi?** - IAM kontrol et
4. **Region aynı mı?** - Tüm servislerde us-central1 kullan

Sistemin tamamı yaklaşık **$1-5/ay** maliyetle çalışır! 🎉 