"""
Cloud Function: Setup Vertex AI
Vertex AI Search Engine kurar ve batch'leri import eder.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List
import functions_framework
from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import discoveryengine
import time

# Logging ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
BUCKET_NAME = os.environ.get('STORAGE_BUCKET_NAME')
PUBSUB_TOPIC = os.environ.get('PUBSUB_TOPIC', 'ai-overview-pipeline')
LOCATION = os.environ.get('LOCATION', 'global')

class VertexAISetup:
    """Vertex AI Discovery Engine setup"""
    
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.discovery_client = discoveryengine.DataStoreServiceClient()
        
    def create_or_get_data_store(self, data_store_id: str) -> str:
        """Data store oluştur veya mevcut olanı al"""
        try:
            parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection"
            
            # Check if data store exists
            try:
                data_store_name = f"{parent}/dataStores/{data_store_id}"
                data_store = self.discovery_client.get_data_store(name=data_store_name)
                logger.info(f"Data store already exists: {data_store.name}")
                return data_store.name
            except Exception:
                # Data store doesn't exist, create it
                pass
            
            # Create data store
            data_store = discoveryengine.DataStore(
                display_name="AI Overview Data Store",
                industry_vertical=discoveryengine.IndustryVertical.GENERIC,
                solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
                content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
            )
            
            operation = self.discovery_client.create_data_store(
                parent=parent,
                data_store=data_store,
                data_store_id=data_store_id
            )
            
            # Wait for operation to complete
            logger.info("Creating data store...")
            result = operation.result(timeout=1200)  # 20 minutes timeout
            
            logger.info(f"Data store created: {result.name}")
            return result.name
            
        except Exception as e:
            logger.error(f"Error creating data store: {str(e)}")
            raise
    
    def import_batch_documents(self, data_store_name: str, batch_files: List[str]) -> Dict:
        """Batch dosyalarını data store'a import et"""
        try:
            import_stats = {
                'total_batches': len(batch_files),
                'successful_imports': 0,
                'failed_imports': 0,
                'import_results': []
            }
            
            for batch_file in batch_files:
                try:
                    logger.info(f"Importing batch: {batch_file}")
                    
                    # Prepare import request
                    gcs_source = discoveryengine.GcsSource(
                        input_uris=[batch_file],
                        data_schema="content"
                    )
                    
                    import_config = discoveryengine.ImportDocumentsRequest.InlineSource(
                        documents=[]
                    )
                    
                    # Use GCS source instead
                    request = discoveryengine.ImportDocumentsRequest(
                        parent=data_store_name,
                        gcs_source=gcs_source,
                        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
                    )
                    
                    # Start import operation
                    operation = self.discovery_client.import_documents(request=request)
                    
                    # Wait for completion (with timeout)
                    try:
                        result = operation.result(timeout=600)  # 10 minutes per batch
                        
                        import_stats['successful_imports'] += 1
                        import_stats['import_results'].append({
                            'batch_file': batch_file,
                            'status': 'success',
                            'operation_name': operation.operation.name
                        })
                        
                        logger.info(f"Successfully imported: {batch_file}")
                        
                    except Exception as e:
                        import_stats['failed_imports'] += 1
                        import_stats['import_results'].append({
                            'batch_file': batch_file,
                            'status': 'failed',
                            'error': str(e)
                        })
                        logger.error(f"Failed to import {batch_file}: {str(e)}")
                        continue
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    import_stats['failed_imports'] += 1
                    import_stats['import_results'].append({
                        'batch_file': batch_file,
                        'status': 'failed',
                        'error': str(e)
                    })
                    logger.error(f"Error processing batch {batch_file}: {str(e)}")
                    continue
            
            return import_stats
            
        except Exception as e:
            logger.error(f"Error importing documents: {str(e)}")
            raise
    
    def save_setup_results(self, results: Dict):
        """Setup sonuçlarını kaydet"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vertex_ai_setup_{timestamp}.json"
            blob_name = f"metadata/{filename}"
            
            blob = self.bucket.blob(blob_name)
            json_data = json.dumps(results, ensure_ascii=False, indent=2)
            blob.upload_from_string(json_data, content_type='application/json')
            
            logger.info(f"Setup results saved to gs://{BUCKET_NAME}/{blob_name}")
            return f"gs://{BUCKET_NAME}/{blob_name}"
            
        except Exception as e:
            logger.error(f"Error saving setup results: {str(e)}")
            raise

@functions_framework.http
def setup_vertex_ai(request):
    """HTTP Cloud Function entry point"""
    
    # CORS headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    headers = {
        'Access-Control-Allow-Origin': '*'
    }
    
    try:
        # Request data'yı al
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return json.dumps({
                'error': 'JSON data required'
            }), 400, headers
        
        batch_files = request_json.get('batch_files', [])
        
        if not batch_files:
            return json.dumps({
                'error': 'batch_files required'
            }), 400, headers
        
        logger.info(f"Starting Vertex AI setup for {len(batch_files)} batch files")
        
        # Setup Vertex AI
        setup = VertexAISetup()
        
        # Create data store
        data_store_id = f"ai-overview-data-{datetime.now().strftime('%Y%m%d')}"
        data_store_name = setup.create_or_get_data_store(data_store_id)
        
        # Import documents
        import_stats = setup.import_batch_documents(data_store_name, batch_files)
        
        # Prepare results
        results = {
            'status': 'success',
            'message': 'Vertex AI setup completed',
            'data_store_name': data_store_name,
            'data_store_id': data_store_id,
            'import_stats': import_stats,
            'setup_completed_at': datetime.now().isoformat(),
            'next_step': 'analyze-content'
        }
        
        # Save results
        setup_file = setup.save_setup_results(results)
        results['setup_file'] = setup_file
        
        # PubSub'a mesaj gönder (sonraki step için)
        try:
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
            
            message_data = {
                'step': 'analyze-content',
                'data_store_name': data_store_name,
                'batch_files': batch_files
            }
            
            publisher.publish(topic_path, json.dumps(message_data).encode('utf-8'))
            logger.info("Message sent to PubSub for next step")
            
        except Exception as e:
            logger.warning(f"Failed to send PubSub message: {str(e)}")
        
        return json.dumps(results), 200, headers
        
    except Exception as e:
        logger.error(f"Function error: {str(e)}")
        return json.dumps({
            'error': f'Internal error: {str(e)}'
        }), 500, headers

@functions_framework.cloud_event
def setup_vertex_ai_pubsub(cloud_event):
    """PubSub triggered version"""
    import base64
    
    # Decode PubSub message
    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
    message_json = json.loads(message_data)
    
    batch_files = message_json.get('batch_files', [])
    
    if not batch_files:
        logger.error("batch_files not provided in PubSub message")
        return
    
    logger.info(f"Starting PubSub-triggered Vertex AI setup for {len(batch_files)} files")
    
    try:
        setup = VertexAISetup()
        
        data_store_id = f"ai-overview-data-{datetime.now().strftime('%Y%m%d')}"
        data_store_name = setup.create_or_get_data_store(data_store_id)
        import_stats = setup.import_batch_documents(data_store_name, batch_files)
        
        results = {
            'status': 'success',
            'data_store_name': data_store_name,
            'import_stats': import_stats,
            'setup_completed_at': datetime.now().isoformat()
        }
        
        setup.save_setup_results(results)
        logger.info(f"PubSub Vertex AI setup completed: {data_store_name}")
        
        # Trigger next step
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
        
        next_message = {
            'step': 'analyze-content',
            'data_store_name': data_store_name,
            'batch_files': batch_files
        }
        
        publisher.publish(topic_path, json.dumps(next_message).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"PubSub function error: {str(e)}")
        raise 