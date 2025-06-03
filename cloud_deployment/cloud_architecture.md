# AI Overview Optimization - Tam Cloud Mimarisi

## 🏗️ Mimari Genel Bakış

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

## 🔧 Bileşenler

### 1. **Cloud Run (Ana Web Uygulaması)**
- Flask/FastAPI web interface
- Proje yönetimi dashboard'u
- Real-time progress tracking
- Sonuç görüntüleme ve indirme

### 2. **Cloud Functions (İşleme Modülleri)**
- `extract-website-data`: Web sitesi veri çıkarma
- `process-batches`: Batch işleme
- `setup-vertex-ai`: Vertex AI kurulumu
- `analyze-content`: AI Overview analizi

### 3. **Cloud Storage (Veri Depolama)**
- Raw data bucket
- Processed data bucket
- Results bucket
- Static assets bucket

### 4. **Cloud Scheduler (Otomasyon)**
- Periyodik veri güncellemeleri
- Otomatik analiz çalıştırma
- Cleanup işlemleri

### 5. **Cloud SQL (Metadata)**
- Proje durumları
- İş geçmişi
- Kullanıcı ayarları
- Analytics verileri

### 6. **Vertex AI (Core AI)**
- Discovery Engine
- Search Engine
- Document processing

## 🚀 Deployment Pipeline

1. **Infrastructure as Code (Terraform)**
2. **CI/CD (Cloud Build)**
3. **Monitoring (Cloud Monitoring)**
4. **Logging (Cloud Logging)**

## 💰 Tahmini Maliyetler

| Servis | Aylık Maliyet (USD) |
|--------|---------------------|
| Cloud Run | $5-20 |
| Cloud Functions | $1-10 |
| Cloud Storage | $2-15 |
| Cloud SQL | $7-25 |
| Vertex AI Search | $10-50 |
| **Toplam** | **$25-120** |

## 🔐 Güvenlik

- IAM rolleri ve permissions
- Service account authentication
- API key management
- Network security policies 