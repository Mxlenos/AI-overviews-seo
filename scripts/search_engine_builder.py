"""
Arama Motoru Kurucusu - AI Overview Projesi
Vertex AI Search üzerinde özel arama motoru oluşturur ve AI Overview analizleri yapar.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta

# Google Cloud kütüphaneleri
try:
    from google.cloud import discoveryengine
    from google.cloud import storage
    from google.auth import default
except ImportError as e:
    print("❌ Google Cloud kütüphaneleri bulunamadı. Lütfen requirements.txt'i yükleyin:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# AI analiz için kütüphaneler
try:
    import pandas as pd
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print("❌ AI analiz kütüphaneleri bulunamadı. Lütfen requirements.txt'i yükleyin:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Proje kök dizinini sys.path'e ekle
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

# Loglama konfigürasyonu
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchEngineBuilder:
    """Arama motoru kurucusu ve AI Overview analiz sınıfı"""
    
    def __init__(self):
        self.project_id = GCP_PROJECT_ID
        self.location = DISCOVERY_ENGINE_LOCATION
        self.storage_client = None
        self.search_client = None
        self.document_client = None
        self.sentence_model = None
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Google Cloud client'larını başlat"""
        try:
            # Kimlik doğrulama
            credentials, project = default()
            logger.info(f"Google Cloud kimlik doğrulaması başarılı: {project}")
            
            # Client'ları başlat
            self.storage_client = storage.Client(project=self.project_id)
            self.search_client = discoveryengine.SearchServiceClient()
            self.document_client = discoveryengine.DocumentServiceClient()
            
            # Sentence transformer modelini yükle
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("Tüm client'lar başarıyla başlatıldı")
            
        except Exception as e:
            logger.error(f"Client başlatma hatası: {str(e)}")
            raise
    
    def import_documents_to_datastore(self, data_store_id: str, batch_files: List[Path]) -> bool:
        """Batch dosyalarını data store'a import eder"""
        logger.info(f"Dokümanlar data store'a import ediliyor: {data_store_id}")
        
        try:
            # Her batch dosyasını işle
            for batch_file in batch_files:
                logger.info(f"Batch dosyası işleniyor: {batch_file}")
                
                # Dosyayı Cloud Storage'a yükle
                bucket_name = STORAGE_BUCKET_NAME
                blob_name = f"{STORAGE_BATCH_PREFIX}/{batch_file.name}"
                
                bucket = self.storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                
                if not blob.exists():
                    blob.upload_from_filename(str(batch_file))
                    logger.info(f"Dosya yüklendi: gs://{bucket_name}/{blob_name}")
                
                # Import işlemi için request oluştur
                request = discoveryengine.ImportDocumentsRequest(
                    parent=f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/dataStores/{data_store_id}/branches/default_branch",
                    gcs_source=discoveryengine.GcsSource(
                        input_uris=[f"gs://{bucket_name}/{blob_name}"],
                        data_schema="document"
                    ),
                    reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
                )
                
                # Import işlemini başlat
                operation = self.document_client.import_documents(request=request)
                logger.info(f"Import işlemi başlatıldı: {batch_file.name}")
                
                # İşlemin tamamlanmasını bekle (opsiyonel)
                try:
                    response = operation.result(timeout=1800)  # 30 dakika timeout
                    logger.info(f"✅ Import tamamlandı: {batch_file.name}")
                except Exception as e:
                    logger.warning(f"Import işlemi timeout oldu, arka planda devam ediyor: {batch_file.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Doküman import hatası: {str(e)}")
            return False
    
    def search_documents(self, engine_id: str, query: str, max_results: int = 10) -> List[Dict]:
        """Arama motoru üzerinde arama yapar"""
        logger.info(f"Arama yapılıyor: '{query}' (max {max_results} sonuç)")
        
        try:
            # Arama isteği oluştur
            request = discoveryengine.SearchRequest(
                serving_config=f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config",
                query=query,
                page_size=max_results,
                query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                    condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO
                ),
                spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                    mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
                ),
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True,
                        max_snippet_count=3
                    ),
                    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                        summary_result_count=5,
                        include_citations=True
                    )
                )
            )
            
            # Arama yap
            response = self.search_client.search(request=request)
            
            results = []
            for result in response.results:
                doc_data = {
                    'id': result.id,
                    'document': result.document.name if result.document else "",
                    'uri': result.document.derived_struct_data.get('link', '') if result.document and result.document.derived_struct_data else "",
                    'title': result.document.derived_struct_data.get('title', '') if result.document and result.document.derived_struct_data else "",
                    'snippet': result.document.derived_struct_data.get('snippet', '') if result.document and result.document.derived_struct_data else "",
                    'relevance_score': getattr(result, 'relevance_score', 0.0)
                }
                results.append(doc_data)
            
            # Summary bilgisi
            summary_info = {
                'total_results': len(results),
                'query': query,
                'search_time': datetime.now().isoformat(),
                'summary': response.summary.summary_text if hasattr(response, 'summary') and response.summary else ""
            }
            
            logger.info(f"✅ Arama tamamlandı: {len(results)} sonuç bulundu")
            
            return {
                'summary': summary_info,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Arama hatası: {str(e)}")
            return {'summary': {}, 'results': []}
    
    def analyze_ai_overview_potential(self, search_results: Dict, target_keywords: List[str]) -> Dict:
        """AI Overview potansiyelini analiz eder"""
        logger.info("AI Overview potansiyeli analiz ediliyor...")
        
        try:
            results = search_results.get('results', [])
            if not results:
                return {'score': 0, 'recommendations': ['Arama sonucu bulunamadı']}
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'total_documents': len(results),
                'ai_overview_score': 0,
                'content_quality_score': 0,
                'keyword_relevance_score': 0,
                'recommendations': [],
                'top_performing_content': [],
                'optimization_suggestions': []
            }
            
            # İçerik kalitesi analizi
            content_texts = []
            titles = []
            for result in results:
                content_texts.append(result.get('snippet', '') + ' ' + result.get('title', ''))
                titles.append(result.get('title', ''))
            
            if content_texts:
                # TF-IDF analizi
                vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
                try:
                    tfidf_matrix = vectorizer.fit_transform(content_texts)
                    feature_names = vectorizer.get_feature_names_out()
                    
                    # En önemli kelimeleri bul
                    mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
                    top_terms = [feature_names[i] for i in mean_scores.argsort()[-10:][::-1]]
                    analysis['top_terms'] = top_terms
                    
                except Exception as e:
                    logger.warning(f"TF-IDF analizi başarısız: {str(e)}")
                    analysis['top_terms'] = []
                
                # Sentence similarity analizi
                try:
                    if target_keywords:
                        query_text = ' '.join(target_keywords)
                        query_embedding = self.sentence_model.encode([query_text])
                        content_embeddings = self.sentence_model.encode(content_texts)
                        
                        similarities = cosine_similarity(query_embedding, content_embeddings)[0]
                        analysis['keyword_relevance_score'] = float(np.mean(similarities))
                        
                        # En alakalı içerikleri bul
                        top_indices = similarities.argsort()[-3:][::-1]
                        analysis['top_performing_content'] = [
                            {
                                'title': titles[i],
                                'similarity_score': float(similarities[i]),
                                'uri': results[i].get('uri', '')
                            }
                            for i in top_indices
                        ]
                    
                except Exception as e:
                    logger.warning(f"Semantic analiz başarısız: {str(e)}")
                    analysis['keyword_relevance_score'] = 0
            
            # İçerik kalitesi skorları
            quality_factors = []
            
            for result in results:
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                # Başlık kalitesi
                title_score = min(len(title.split()), 10) / 10 if title else 0
                
                # İçerik uzunluğu
                content_length_score = min(len(snippet.split()), 50) / 50 if snippet else 0
                
                # Relevans skoru
                relevance_score = result.get('relevance_score', 0)
                
                quality_score = (title_score + content_length_score + relevance_score) / 3
                quality_factors.append(quality_score)
            
            analysis['content_quality_score'] = float(np.mean(quality_factors)) if quality_factors else 0
            
            # Genel AI Overview skoru
            analysis['ai_overview_score'] = (
                analysis['content_quality_score'] * 0.4 +
                analysis['keyword_relevance_score'] * 0.6
            )
            
            # Öneriler oluştur
            if analysis['ai_overview_score'] < 0.3:
                analysis['recommendations'].extend([
                    "İçerik kalitesini artırın",
                    "Daha uzun ve detaylı açıklamalar ekleyin",
                    "Hedef anahtar kelimelerle daha uyumlu içerik oluşturun"
                ])
            elif analysis['ai_overview_score'] < 0.6:
                analysis['recommendations'].extend([
                    "Başlıkları optimize edin",
                    "Meta açıklamaları geliştirin",
                    "Yapılandırılmış veri ekleyin"
                ])
            else:
                analysis['recommendations'].extend([
                    "Mevcut kaliteyi koruyun",
                    "İçerikleri düzenli olarak güncelleyin",
                    "Yeni anahtar kelimeler için genişletme yapın"
                ])
            
            # Optimizasyon önerileri
            analysis['optimization_suggestions'] = [
                "H1-H6 başlık yapısını iyileştirin",
                "FAQ bölümleri ekleyin",
                "Listeleme formatını kullanın",
                "Doğrudan cevap veren paragraflar yazın",
                "İstatistikler ve veri noktaları ekleyin"
            ]
            
            logger.info(f"✅ AI Overview analizi tamamlandı. Skor: {analysis['ai_overview_score']:.2f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ AI Overview analiz hatası: {str(e)}")
            return {'score': 0, 'recommendations': ['Analiz sırasında hata oluştu']}
    
    def generate_optimization_report(self, analysis: Dict, search_results: Dict) -> str:
        """Optimizasyon raporu oluşturur"""
        report_lines = [
            "# AI OVERVIEW OPTİMİZASYON RAPORU",
            f"Oluşturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50,
            "",
            "## GENEL DURUM",
            f"AI Overview Skoru: {analysis.get('ai_overview_score', 0):.1%}",
            f"İçerik Kalitesi: {analysis.get('content_quality_score', 0):.1%}",
            f"Anahtar Kelime Uyumu: {analysis.get('keyword_relevance_score', 0):.1%}",
            f"Toplam Doküman: {analysis.get('total_documents', 0)}",
            "",
            "## EN ÇOK KULLANTLAN KELİMELER",
        ]
        
        # En çok kullanılan kelimeler
        top_terms = analysis.get('top_terms', [])
        for i, term in enumerate(top_terms[:5], 1):
            report_lines.append(f"{i}. {term}")
        
        report_lines.extend([
            "",
            "## EN İYİ PERFORMANS GÖSTEREN İÇERİKLER",
        ])
        
        # En iyi içerikler
        top_content = analysis.get('top_performing_content', [])
        for i, content in enumerate(top_content, 1):
            report_lines.extend([
                f"{i}. {content.get('title', 'Başlık yok')}",
                f"   Benzerlik Skoru: {content.get('similarity_score', 0):.1%}",
                f"   URL: {content.get('uri', 'URL yok')}",
                ""
            ])
        
        report_lines.extend([
            "## ÖNERİLER",
        ])
        
        # Öneriler
        recommendations = analysis.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        
        report_lines.extend([
            "",
            "## OPTİMİZASYON ÖNERİLERİ",
        ])
        
        # Optimizasyon önerileri
        suggestions = analysis.get('optimization_suggestions', [])
        for i, suggestion in enumerate(suggestions, 1):
            report_lines.append(f"{i}. {suggestion}")
        
        return "\n".join(report_lines)
    
    def save_analysis_results(self, analysis: Dict, search_results: Dict, filename: str = None) -> Path:
        """Analiz sonuçlarını dosyaya kaydeder"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ai_overview_analysis_{timestamp}.json"
        
        # Analiz sonuçları
        results = {
            'analysis': analysis,
            'search_results': search_results,
            'generated_at': datetime.now().isoformat(),
            'project_id': self.project_id
        }
        
        # JSON dosyası kaydet
        filepath = PROCESSED_DATA_DIR / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Rapor dosyası kaydet
        report_filename = filename.replace('.json', '_report.txt')
        report_filepath = PROCESSED_DATA_DIR / report_filename
        
        report_text = self.generate_optimization_report(analysis, search_results)
        with open(report_filepath, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"Analiz sonuçları kaydedildi: {filepath}")
        logger.info(f"Rapor kaydedildi: {report_filepath}")
        
        return filepath

def main():
    """Ana fonksiyon - komut satırından çalıştırma"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Overview arama motoru analizi')
    parser.add_argument('--engine-id', required=True, help='Search engine ID')
    parser.add_argument('--data-store-id', help='Data store ID (import için)')
    parser.add_argument('--query', required=True, help='Arama sorgusu')
    parser.add_argument('--keywords', nargs='+', help='Hedef anahtar kelimeler')
    parser.add_argument('--batch-files', nargs='+', help='Import edilecek batch dosyaları')
    parser.add_argument('--import-only', action='store_true', help='Sadece import işlemi yap')
    
    args = parser.parse_args()
    
    # Search engine builder başlat
    builder = SearchEngineBuilder()
    
    try:
        # Batch dosyalarını import et (gerekirse)
        if args.batch_files and args.data_store_id:
            batch_paths = [Path(f) for f in args.batch_files]
            logger.info("Batch dosyaları import ediliyor...")
            success = builder.import_documents_to_datastore(args.data_store_id, batch_paths)
            
            if not success:
                print("❌ Import işlemi başarısız!")
                return
            
            if args.import_only:
                print("✅ Import işlemi tamamlandı!")
                return
        
        # Arama yap
        print(f"\n🔍 Arama yapılıyor: '{args.query}'")
        search_results = builder.search_documents(args.engine_id, args.query)
        
        if not search_results.get('results'):
            print("❌ Arama sonucu bulunamadı!")
            return
        
        # AI Overview analizi
        print(f"\n🤖 AI Overview analizi yapılıyor...")
        keywords = args.keywords or [args.query]
        analysis = builder.analyze_ai_overview_potential(search_results, keywords)
        
        # Sonuçları kaydet
        result_file = builder.save_analysis_results(analysis, search_results)
        
        # Özet rapor
        print(f"\n📊 ANALIZ SONUÇLARI")
        print(f"{'='*40}")
        print(f"AI Overview Skoru: {analysis.get('ai_overview_score', 0):.1%}")
        print(f"İçerik Kalitesi: {analysis.get('content_quality_score', 0):.1%}")
        print(f"Anahtar Kelime Uyumu: {analysis.get('keyword_relevance_score', 0):.1%}")
        print(f"Bulunan Doküman Sayısı: {len(search_results.get('results', []))}")
        
        print(f"\n💡 EN ÖNEMLİ ÖNERİLER:")
        recommendations = analysis.get('recommendations', [])
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n📁 Detaylı rapor: {result_file}")
        print(f"📄 Metin raporu: {result_file.with_suffix('')}_report.txt")
        
    except Exception as e:
        logger.error(f"İşlem hatası: {str(e)}")
        print(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    main() 