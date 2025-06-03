"""
Cloud Function: Process Batches
Ham verileri 50'şer URL'lik batch'lere böler ve Cloud Storage'a kaydeder.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List
import functions_framework
from google.cloud import storage
from google.cloud import pubsub_v1
from math import ceil

# Logging ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
BUCKET_NAME = os.environ.get('STORAGE_BUCKET_NAME')
PUBSUB_TOPIC = os.environ.get('PUBSUB_TOPIC', 'ai-overview-pipeline')
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '50'))

class CloudBatchProcessor:
    """Cloud-based batch processor"""
    
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        
    def load_raw_data(self, raw_data_file: str) -> List[Dict]:
        """Cloud Storage'dan ham veriyi yükle"""
        try:
            blob_name = f"raw_data/{raw_data_file}"
            blob = self.bucket.blob(blob_name)
            
            if not blob.exists():
                raise FileNotFoundError(f"Raw data file not found: {blob_name}")
            
            json_data = blob.download_as_text()
            data = json.loads(json_data)
            
            logger.info(f"Loaded {len(data)} records from {blob_name}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading raw data: {str(e)}")
            raise
    
    def validate_data(self, data: List[Dict]) -> List[Dict]:
        """Veri validasyonu ve temizleme"""
        valid_data = []
        
        for item in data:
            # Gerekli alanları kontrol et
            if not all(key in item for key in ['url', 'title', 'content']):
                logger.warning(f"Skipping invalid item: missing required fields")
                continue
            
            # Content uzunluğu kontrolü
            content = item.get('content', '')
            word_count = len(content.split())
            
            if word_count < 10:  # Minimum word count
                logger.warning(f"Skipping {item['url']}: content too short ({word_count} words)")
                continue
                
            if word_count > 10000:  # Maximum word count
                # Truncate content
                words = content.split()[:10000]
                item['content'] = ' '.join(words)
                item['truncated'] = True
                logger.info(f"Truncated content for {item['url']}")
            
            # URL validation
            url = item.get('url', '')
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"Skipping invalid URL: {url}")
                continue
            
            valid_data.append(item)
        
        logger.info(f"Validated {len(valid_data)} out of {len(data)} records")
        return valid_data
    
    def create_batches(self, data: List[Dict]) -> List[str]:
        """Verileri batch'lere böl ve Cloud Storage'a kaydet"""
        
        if not data:
            logger.warning("No data to process")
            return []
        
        # Validate data first
        valid_data = self.validate_data(data)
        
        if not valid_data:
            logger.warning("No valid data after validation")
            return []
        
        # Calculate number of batches
        num_batches = ceil(len(valid_data) / BATCH_SIZE)
        batch_files = []
        
        logger.info(f"Creating {num_batches} batches from {len(valid_data)} records")
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(valid_data))
            
            batch_data = valid_data[start_idx:end_idx]
            
            # Create batch file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            batch_filename = f"batch_{batch_idx + 1:03d}_{timestamp}.json"
            
            # Prepare batch content for Vertex AI
            vertex_ai_batch = []
            for item in batch_data:
                vertex_ai_item = {
                    "id": f"doc_{start_idx + i}",
                    "structData": {
                        "url": item['url'],
                        "title": item['title'],
                        "content": item['content'],
                        "description": item.get('description', ''),
                        "word_count": item.get('word_count', len(item['content'].split())),
                        "extracted_at": item.get('extracted_at', datetime.now().isoformat())
                    },
                    "content": {
                        "mimeType": "text/plain",
                        "uri": item['url']
                    }
                }
                vertex_ai_batch.append(vertex_ai_item)
            
            # Save to Cloud Storage
            batch_path = self.save_batch_to_storage(vertex_ai_batch, batch_filename)
            batch_files.append(batch_path)
            
            logger.info(f"Created batch {batch_idx + 1}/{num_batches}: {batch_filename} ({len(batch_data)} items)")
        
        # Save batch metadata
        metadata = {
            'total_batches': num_batches,
            'total_items': len(valid_data),
            'batch_size': BATCH_SIZE,
            'created_at': datetime.now().isoformat(),
            'batch_files': batch_files
        }
        
        metadata_filename = f"batch_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.save_metadata_to_storage(metadata, metadata_filename)
        
        return batch_files
    
    def save_batch_to_storage(self, batch_data: List[Dict], filename: str) -> str:
        """Batch'i Cloud Storage'a kaydet"""
        try:
            blob_name = f"batches/{filename}"
            blob = self.bucket.blob(blob_name)
            
            # Convert to JSONL format for Vertex AI
            jsonl_content = '\n'.join(json.dumps(item, ensure_ascii=False) for item in batch_data)
            blob.upload_from_string(jsonl_content, content_type='application/jsonl')
            
            storage_path = f"gs://{BUCKET_NAME}/{blob_name}"
            logger.info(f"Batch saved to {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Error saving batch: {str(e)}")
            raise
    
    def save_metadata_to_storage(self, metadata: Dict, filename: str):
        """Metadata'yı Cloud Storage'a kaydet"""
        try:
            blob_name = f"metadata/{filename}"
            blob = self.bucket.blob(blob_name)
            
            json_data = json.dumps(metadata, ensure_ascii=False, indent=2)
            blob.upload_from_string(json_data, content_type='application/json')
            
            logger.info(f"Metadata saved to gs://{BUCKET_NAME}/{blob_name}")
            
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            raise

@functions_framework.http
def process_batches(request):
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
        
        data_file = request_json.get('data_file')
        
        if not data_file:
            return json.dumps({
                'error': 'data_file required'
            }), 400, headers
        
        logger.info(f"Starting batch processing for file: {data_file}")
        
        # Processor'ı başlat
        processor = CloudBatchProcessor()
        
        # Ham verileri yükle
        raw_data = processor.load_raw_data(data_file)
        
        # Batch'lere böl
        batch_files = processor.create_batches(raw_data)
        
        # Sonuç
        result = {
            'status': 'success',
            'message': 'Batch processing completed',
            'stats': {
                'input_records': len(raw_data),
                'batches_created': len(batch_files),
                'batch_size': BATCH_SIZE
            },
            'batch_files': batch_files,
            'next_step': 'setup-vertex-ai'
        }
        
        # PubSub'a mesaj gönder (sonraki step için)
        try:
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
            
            message_data = {
                'step': 'setup-vertex-ai',
                'batch_files': batch_files,
                'data_file': data_file
            }
            
            publisher.publish(topic_path, json.dumps(message_data).encode('utf-8'))
            logger.info("Message sent to PubSub for next step")
            
        except Exception as e:
            logger.warning(f"Failed to send PubSub message: {str(e)}")
        
        return json.dumps(result), 200, headers
        
    except Exception as e:
        logger.error(f"Function error: {str(e)}")
        return json.dumps({
            'error': f'Internal error: {str(e)}'
        }), 500, headers

@functions_framework.cloud_event
def process_batches_pubsub(cloud_event):
    """PubSub triggered version"""
    import base64
    
    # Decode PubSub message
    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
    message_json = json.loads(message_data)
    
    data_file = message_json.get('data_file')
    
    if not data_file:
        logger.error("data_file not provided in PubSub message")
        return
    
    logger.info(f"Starting PubSub-triggered batch processing for file: {data_file}")
    
    try:
        processor = CloudBatchProcessor()
        raw_data = processor.load_raw_data(data_file)
        batch_files = processor.create_batches(raw_data)
        
        logger.info(f"PubSub batch processing completed: {len(batch_files)} batches created")
        
        # Trigger next step
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
        
        next_message = {
            'step': 'setup-vertex-ai',
            'batch_files': batch_files,
            'data_file': data_file
        }
        
        publisher.publish(topic_path, json.dumps(next_message).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"PubSub function error: {str(e)}")
        raise 