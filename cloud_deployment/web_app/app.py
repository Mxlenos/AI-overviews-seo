"""
AI Overview Optimization - Cloud Run Web Application
Tamamen cloud-based web interface ve dashboard
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import sql
from google.cloud import discoveryengine
import requests
from typing import Dict, List, Optional

# Logging ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
BUCKET_NAME = os.environ.get('STORAGE_BUCKET_NAME')
PUBSUB_TOPIC = os.environ.get('PUBSUB_TOPIC', 'ai-overview-pipeline')
CLOUD_FUNCTION_REGION = os.environ.get('CLOUD_FUNCTION_REGION', 'us-central1')

# Cloud Function URLs (deployed olduğunda set edilecek)
EXTRACT_FUNCTION_URL = os.environ.get('EXTRACT_FUNCTION_URL', '')
PROCESS_FUNCTION_URL = os.environ.get('PROCESS_FUNCTION_URL', '')
VERTEX_FUNCTION_URL = os.environ.get('VERTEX_FUNCTION_URL', '')
ANALYZE_FUNCTION_URL = os.environ.get('ANALYZE_FUNCTION_URL', '')

class CloudDashboard:
    """Cloud dashboard manager"""
    
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.publisher = pubsub_v1.PublisherClient()
        
    def get_project_status(self) -> Dict:
        """Proje durumunu al"""
        try:
            # Check recent files in Cloud Storage
            blobs = list(self.bucket.list_blobs(prefix='raw_data/', max_results=10))
            recent_extractions = []
            
            for blob in blobs:
                if blob.name.endswith('.json'):
                    recent_extractions.append({
                        'file': blob.name.split('/')[-1],
                        'created': blob.time_created.isoformat(),
                        'size': blob.size
                    })
            
            # Check batch files
            batch_blobs = list(self.bucket.list_blobs(prefix='batches/', max_results=20))
            recent_batches = len(batch_blobs)
            
            # Check processed results
            result_blobs = list(self.bucket.list_blobs(prefix='results/', max_results=10))
            recent_results = []
            
            for blob in result_blobs:
                if blob.name.endswith('.json'):
                    recent_results.append({
                        'file': blob.name.split('/')[-1],
                        'created': blob.time_created.isoformat(),
                        'size': blob.size
                    })
            
            return {
                'status': 'active',
                'recent_extractions': recent_extractions,
                'recent_batches': recent_batches,
                'recent_results': recent_results,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting project status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
    def trigger_extraction(self, url: str, max_pages: int = 100) -> Dict:
        """Veri çıkarma işlemini başlat"""
        try:
            if EXTRACT_FUNCTION_URL:
                # HTTP Cloud Function çağır
                response = requests.post(EXTRACT_FUNCTION_URL, json={
                    'url': url,
                    'max_pages': max_pages
                }, timeout=300)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        'status': 'error',
                        'error': f'Function returned {response.status_code}: {response.text}'
                    }
            else:
                # PubSub mesajı gönder
                topic_path = self.publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
                message_data = {
                    'step': 'extract-website-data',
                    'url': url,
                    'max_pages': max_pages
                }
                
                self.publisher.publish(topic_path, json.dumps(message_data).encode('utf-8'))
                
                return {
                    'status': 'started',
                    'message': 'Extraction process started via PubSub',
                    'url': url,
                    'max_pages': max_pages
                }
                
        except Exception as e:
            logger.error(f"Error triggering extraction: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_analysis_results(self, limit: int = 10) -> List[Dict]:
        """Analiz sonuçlarını al"""
        try:
            blobs = list(self.bucket.list_blobs(
                prefix='results/', 
                max_results=limit
            ))
            
            results = []
            for blob in blobs:
                if blob.name.endswith('.json') and 'analysis' in blob.name:
                    try:
                        content = blob.download_as_text()
                        data = json.loads(content)
                        
                        # Extract summary info
                        analysis = data.get('analysis', {})
                        summary = {
                            'file': blob.name.split('/')[-1],
                            'created': blob.time_created.isoformat(),
                            'ai_overview_score': analysis.get('ai_overview_score', 0),
                            'content_quality_score': analysis.get('content_quality_score', 0),
                            'keyword_relevance_score': analysis.get('keyword_relevance_score', 0),
                            'total_documents': analysis.get('total_documents', 0),
                            'blob_name': blob.name
                        }
                        results.append(summary)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing result file {blob.name}: {str(e)}")
                        continue
            
            # Sort by creation date (newest first)
            results.sort(key=lambda x: x['created'], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error getting analysis results: {str(e)}")
            return []
    
    def get_detailed_result(self, blob_name: str) -> Optional[Dict]:
        """Detaylı analiz sonucunu al"""
        try:
            blob = self.bucket.blob(blob_name)
            if blob.exists():
                content = blob.download_as_text()
                return json.loads(content)
            return None
            
        except Exception as e:
            logger.error(f"Error getting detailed result: {str(e)}")
            return None

# Dashboard instance
dashboard = CloudDashboard()

@app.route('/')
def index():
    """Ana dashboard sayfası"""
    try:
        status = dashboard.get_project_status()
        recent_results = dashboard.get_analysis_results(5)
        
        return render_template('dashboard.html', 
                             status=status, 
                             recent_results=recent_results)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/status')
def api_status():
    """API: Proje durumu"""
    return jsonify(dashboard.get_project_status())

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """API: Veri çıkarma başlat"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL required'}), 400
        
        url = data['url']
        max_pages = data.get('max_pages', 100)
        
        result = dashboard.trigger_extraction(url, max_pages)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in extract API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/results')
def api_results():
    """API: Analiz sonuçları listesi"""
    try:
        limit = request.args.get('limit', 10, type=int)
        results = dashboard.get_analysis_results(limit)
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in results API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/result/<path:blob_name>')
def api_result_detail(blob_name):
    """API: Detaylı analiz sonucu"""
    try:
        result = dashboard.get_detailed_result(blob_name)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Result not found'}), 404
            
    except Exception as e:
        logger.error(f"Error in result detail API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/extract')
def extract_page():
    """Veri çıkarma sayfası"""
    return render_template('extract.html')

@app.route('/results')
def results_page():
    """Sonuçlar sayfası"""
    try:
        results = dashboard.get_analysis_results(20)
        return render_template('results.html', results=results)
    except Exception as e:
        logger.error(f"Error loading results page: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/result/<path:blob_name>')
def result_detail_page(blob_name):
    """Detaylı sonuç sayfası"""
    try:
        result = dashboard.get_detailed_result(blob_name)
        if result:
            return render_template('result_detail.html', result=result, blob_name=blob_name)
        else:
            return render_template('error.html', error='Result not found'), 404
            
    except Exception as e:
        logger.error(f"Error loading result detail: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'project_id': PROJECT_ID,
        'bucket': BUCKET_NAME
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 