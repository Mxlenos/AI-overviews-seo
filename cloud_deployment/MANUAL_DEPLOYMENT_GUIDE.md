# 🚀 AI Overview Optimization - Manuel Cloud Deployment Rehberi

## 📋 Önkoşullar
- Google Cloud Console'a erişim: https://console.cloud.google.com
- Proje ID: `ai-overviews-v1`
- Billing etkin olmalı

## 1️⃣ API'leri Etkinleştir

Google Cloud Console'da şu sayfaya gidin:
**APIs & Services > Library**

Aşağıdaki API'leri arayıp **ENABLE** edin:

1. ✅ **Cloud Functions API**
2. ✅ **Cloud Run API** 
3. ✅ **Cloud Storage API**
4. ✅ **Pub/Sub API**
5. ✅ **Discovery Engine API**
6. ✅ **Cloud Build API**
7. ✅ **Artifact Registry API**
8. ✅ **Cloud Logging API**
9. ✅ **Cloud Monitoring API**

## 2️⃣ Cloud Storage Bucket Oluştur

**Storage > Buckets** sayfasına gidin:

1. **CREATE BUCKET** tıklayın
2. **Bucket name:** `ai-overviews-v1-ai-overview-data`
3. **Location:** `us-central1` (Region)
4. **Storage class:** Standard
5. **Access control:** Uniform
6. **CREATE** tıklayın

Bucket oluşturulduktan sonra içine şu klasörleri ekleyin:
- `raw_data/`
- `batches/`
- `results/`
- `metadata/`
- `temp/`

## 3️⃣ Cloud Functions Deploy Et

### 3.1 Extract Website Data Function

**Cloud Functions** sayfasına gidin:

1. **CREATE FUNCTION** tıklayın
2. **Function name:** `extract-website-data`
3. **Region:** `us-central1`
4. **Trigger type:** HTTP
5. **Authentication:** Allow unauthenticated invocations
6. **NEXT** tıklayın

**Code** sekmesinde:
1. **Runtime:** Python 3.11
2. **Entry point:** `extract_website_data`
3. **Source code:** Zip upload veya Inline editor

**Environment variables:**
```
GCP_PROJECT_ID = ai-overviews-v1
STORAGE_BUCKET_NAME = ai-overviews-v1-ai-overview-data
PUBSUB_TOPIC = ai-overview-pipeline
```

### 3.2 Process Batches Function

Aynı şekilde:
1. **Function name:** `process-batches`
2. **Entry point:** `process_batches`
3. Aynı environment variables

### 3.3 Setup Vertex AI Function

1. **Function name:** `setup-vertex-ai`
2. **Entry point:** `setup_vertex_ai`
3. **Timeout:** 540 seconds
4. **Memory:** 1GB

## 4️⃣ Cloud Run Web App Deploy Et

**Cloud Run** sayfasına gidin:

1. **CREATE SERVICE** tıklayın
2. **Deploy one revision from an existing container image:** Hayır
3. **Source:** Upload (ZIP file)
4. **Service name:** `ai-overview-web-app`
5. **Region:** `us-central1`

**Container sekmesi:**
- **Port:** 8080
- **Container command:** python app.py

**Environment variables:**
```
GCP_PROJECT_ID = ai-overviews-v1
STORAGE_BUCKET_NAME = ai-overviews-v1-ai-overview-data
PUBSUB_TOPIC = ai-overview-pipeline
EXTRACT_FUNCTION_URL = [Extract function URL'si]
PROCESS_FUNCTION_URL = [Process function URL'si]
```

## 5️⃣ PubSub Topic Oluştur

**Pub/Sub > Topics** sayfasına gidin:

1. **CREATE TOPIC** tıklayın
2. **Topic ID:** `ai-overview-pipeline`
3. **CREATE** tıklayın

## 6️⃣ IAM Permissions Ayarla

**IAM & Admin > IAM** sayfasında:

Cloud Functions ve Cloud Run service account'larına şu rolleri verin:
- Storage Admin
- Pub/Sub Editor  
- Discovery Engine Admin
- Logging Log Writer

## 7️⃣ Test Et

1. Web app URL'ine gidin
2. Dashboard'u kontrol edin
3. Extract sayfasından test analizi başlatın

## 🎯 Başarı!

Tüm adımlar tamamlandığında sisteminiz çalışır durumda olacak!

---

## 📞 Sorun Çözme

### Cloud Function Deploy Hataları
- Timeout süresini artırın (540s)
- Memory'yi artırın (1GB)
- Requirements.txt'yi kontrol edin

### Permissions Hataları
- Service account'ları kontrol edin
- IAM rollerini doğrulayın
- API'lerin enable olduğunu kontrol edin

### Storage Hataları  
- Bucket isminin doğru olduğunu kontrol edin
- Bucket permissions'ı kontrol edin
- Region'ın aynı olduğunu kontrol edin 