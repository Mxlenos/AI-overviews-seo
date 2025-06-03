# AI Overview Optimization - Cloud Deployment

Bu dokümantasyon, **tamamen Google Cloud'da çalışan** AI Overview optimizasyon projesinin kurulumu ve kullanımı için hazırlanmıştır.

## 🎯 Cloud-Native Mimari

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cloud Run     │    │  Cloud Functions │    │ Vertex AI Search│
│  (Web Interface)│────│   (Processing)   │────│    Engine       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Cloud Storage  │    │  Cloud Scheduler │    │   Cloud SQL     │
│   (Data Store)  │    │  (Automation)    │    │  (Metadata)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Hızlı Başlangıç

### 1. Ön Gereksinimler

- Google Cloud hesabı ve aktif proje
- Aşağıdaki araçların kurulu olması:
  - [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
  - [Terraform](https://terraform.io/downloads)
  - [Docker](https://docs.docker.com/get-docker/)

### 2. Tek Komut Deployment

```bash
# Repository'yi klonlayın
git clone <your-repo-url>
cd ai_overview_project/cloud_deployment

# Deployment script'ini çalıştırın
chmod +x deploy.sh
./deploy.sh
```

Bu script:
- ✅ Tüm gerekli Google Cloud API'leri etkinleştirir
- ✅ Infrastructure'ı Terraform ile deploy eder
- ✅ Cloud Functions'ları deploy eder
- ✅ Web uygulamasını Cloud Run'da başlatır
- ✅ Monitoring ve alerting'i kurar

### 3. Manual Deployment (Adım Adım)

Eğer tek komutla deployment yapmak istemezseniz:

#### a) Infrastructure Setup
```bash
cd terraform
terraform init
terraform plan -var="project_id=YOUR_PROJECT_ID"
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

#### b) Cloud Functions Deployment
```bash
cd functions/extract_website_data
gcloud functions deploy extract-website-data \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=extract_website_data \
  --trigger=http

# Diğer functions için benzer şekilde...
```

#### c) Web App Deployment
```bash
cd web_app
gcloud run deploy ai-overview-web-app \
  --source=. \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

## 🌐 Kullanım

### Web Dashboard

Deployment tamamlandıktan sonra Cloud Run URL'ine erişin:

```
https://ai-overview-web-app-XXXXX-uc.a.run.app
```

### Dashboard Özellikleri

1. **📊 Ana Dashboard**
   - Proje durumu görüntüleme
   - Son analizler
   - Sistem metrikleri

2. **🔍 Veri Çıkarma**
   - Web sitesi URL'i girme
   - Maksimum sayfa sayısı belirleme
   - İşlem durumu takip etme

3. **📈 Sonuçlar**
   - AI Overview skorları
   - İçerik kalitesi analizleri
   - Optimizasyon önerileri
   - Detaylı raporlar

### API Kullanımı

REST API endpoint'leri:

```bash
# Veri çıkarma başlat
curl -X POST "https://YOUR_CLOUD_RUN_URL/api/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_pages": 50}'

# Sonuçları listele
curl "https://YOUR_CLOUD_RUN_URL/api/results"

# Detaylı sonuç al
curl "https://YOUR_CLOUD_RUN_URL/api/result/RESULT_ID"
```

## 🔧 Konfigürasyon

### Environment Variables

Cloud Functions ve Cloud Run için önemli environment variable'lar:

```bash
GCP_PROJECT_ID=your-project-id
STORAGE_BUCKET_NAME=your-bucket-name
PUBSUB_TOPIC=ai-overview-pipeline
BATCH_SIZE=50
```

### Terraform Variables

`terraform/terraform.tfvars` dosyasında:

```hcl
project_id  = "your-project-id"
region      = "us-central1"
environment = "dev"
```

## 🔍 Monitoring ve Loglama

### Cloud Logging

```bash
# Function logs
gcloud logging read "resource.type=cloud_function" --limit=50

# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

### Cloud Monitoring

Dashboard'a erişim:
```
https://console.cloud.google.com/monitoring
```

### Alert Policies

Otomatik olarak kurulan alertler:
- Cloud Function error rate > 5%
- Cloud Run instance crashes
- Storage quota warnings

## 📊 Maliyet Optimizasyonu

### Tahmini Aylık Maliyetler

| Servis | Düşük Kullanım | Orta Kullanım | Yüksek Kullanım |
|--------|----------------|---------------|-----------------|
| Cloud Run | $5-10 | $10-25 | $25-50 |
| Cloud Functions | $1-5 | $5-15 | $15-30 |
| Cloud Storage | $2-5 | $5-15 | $15-40 |
| Vertex AI Search | $10-20 | $20-50 | $50-100 |
| **Toplam** | **$18-40** | **$40-105** | **$105-220** |

### Maliyet Azaltma İpuçları

1. **Cleanup Policies**: Eski dosyaları otomatik sil
2. **Function Concurrency**: Eş zamanlı çalışma limitlerini ayarla
3. **Storage Class**: Eski verileri NEARLINE/COLDLINE'a taşı
4. **Region Selection**: En yakın region'ı seç

## 🛠️ Troubleshooting

### Yaygın Sorunlar

#### 1. Deployment Hataları
```bash
# API'lerin etkin olup olmadığını kontrol et
gcloud services list --enabled

# IAM permissions kontrol et
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

#### 2. Function Timeout'ları
```bash
# Function timeout'ını artır
gcloud functions deploy FUNCTION_NAME --timeout=540s
```

#### 3. Storage Permission Hataları
```bash
# Service account'a storage admin rolü ver
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.admin"
```

### Debug Komutları

```bash
# Function logs
gcloud functions logs read extract-website-data --limit=100

# Cloud Run logs
gcloud run services logs ai-overview-web-app --limit=100

# Storage bucket içeriği
gsutil ls -la gs://YOUR_BUCKET_NAME/
```

## 🔄 Güncelleme ve Maintenance

### Code Updates

```bash
# Functions güncelle
gcloud functions deploy FUNCTION_NAME --source=.

# Web app güncelle
gcloud run deploy ai-overview-web-app --source=.
```

### Infrastructure Updates

```bash
cd terraform
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### Backup Stratejisi

1. **Code**: Git repository'de version control
2. **Data**: Cloud Storage versioning enabled
3. **Database**: Automated daily backups
4. **Infrastructure**: Terraform state files

## 🚫 Cleanup (Tam Silme)

Tüm kaynakları silmek için:

```bash
# Terraform ile infrastructure sil
cd terraform
terraform destroy -var-file=terraform.tfvars

# Manuel olarak kalan kaynakları kontrol et
gcloud projects list-gcp-resources YOUR_PROJECT_ID
```

## 📞 Destek

### Google Cloud Console

Tüm servisler için monitoring:
```
https://console.cloud.google.com/
```

### Useful Links

- [Cloud Functions Documentation](https://cloud.google.com/functions/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Search Documentation](https://cloud.google.com/generative-ai-app-builder/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest)

## 🎉 Son Adımlar

1. Web dashboard'a erişin
2. İlk web sitenizi analiz edin
3. Sonuçları inceleyin
4. Monitoring'i kontrol edin

**Artık tamamen cloud-based AI Overview optimizasyon sisteminiz hazır!** 🚀

---

*Bu proje tamamen Google Cloud'da çalışır ve hiçbir lokal dependency gerektirmez.* 