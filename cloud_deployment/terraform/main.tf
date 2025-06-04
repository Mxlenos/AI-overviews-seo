# AI Overview Optimization - Terraform Infrastructure
# Tamamen cloud-based deployment için gerekli tüm kaynaklar

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Google Cloud Zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "discoveryengine.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "secretmanager.googleapis.com",
    "scheduler.googleapis.com",
    "sqladmin.googleapis.com"
  ])

  service = each.value
  project = var.project_id

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Cloud Storage Buckets
resource "google_storage_bucket" "ai_overview_data" {
  name          = "${var.project_id}-ai-overview-data"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Storage bucket folders (simulated with objects)
resource "google_storage_bucket_object" "folders" {
  for_each = toset([
    "raw_data/",
    "batches/",
    "results/",
    "metadata/",
    "temp/"
  ])

  name   = each.value
  bucket = google_storage_bucket.ai_overview_data.name
  content = ""
}

# PubSub Topic for pipeline orchestration
resource "google_pubsub_topic" "ai_overview_pipeline" {
  name = "ai-overview-pipeline"

  depends_on = [google_project_service.required_apis]
}

# PubSub Subscriptions
resource "google_pubsub_subscription" "extract_subscription" {
  name  = "extract-website-data-sub"
  topic = google_pubsub_topic.ai_overview_pipeline.name

  ack_deadline_seconds = 600
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_subscription" "process_subscription" {
  name  = "process-batches-sub"
  topic = google_pubsub_topic.ai_overview_pipeline.name

  ack_deadline_seconds = 600
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_subscription" "vertex_subscription" {
  name  = "setup-vertex-ai-sub"
  topic = google_pubsub_topic.ai_overview_pipeline.name

  ack_deadline_seconds = 1200
  
  retry_policy {
    minimum_backoff = "30s"
    maximum_backoff = "600s"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_subscription" "analyze_subscription" {
  name  = "analyze-content-sub"
  topic = google_pubsub_topic.ai_overview_pipeline.name

  ack_deadline_seconds = 900
  
  retry_policy {
    minimum_backoff = "15s"
    maximum_backoff = "300s"
  }

  depends_on = [google_project_service.required_apis]
}

# Service Account for Cloud Functions
resource "google_service_account" "cloud_functions_sa" {
  account_id   = "ai-overview-functions"
  display_name = "AI Overview Cloud Functions Service Account"
  description  = "Service account for AI Overview cloud functions"

  depends_on = [google_project_service.required_apis]
}

# IAM bindings for Service Account
resource "google_project_iam_member" "function_permissions" {
  for_each = toset([
    "roles/storage.admin",
    "roles/pubsub.editor",
    "roles/discoveryengine.admin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudsql.client"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "ai-overview-web-app"
  display_name = "AI Overview Web App Service Account"
  description  = "Service account for AI Overview web application"

  depends_on = [google_project_service.required_apis]
}

# IAM bindings for Cloud Run Service Account
resource "google_project_iam_member" "web_app_permissions" {
  for_each = toset([
    "roles/storage.admin",
    "roles/pubsub.editor",
    "roles/discoveryengine.viewer",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudsql.client"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "ai_overview_repo" {
  location      = var.region
  repository_id = "ai-overview"
  description   = "AI Overview container repository"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "flask_secret_key" {
  secret_id = "flask-secret-key"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "flask_secret_key_version" {
  secret      = google_secret_manager_secret.flask_secret_key.id
  secret_data = random_password.flask_secret.result
}

resource "random_password" "flask_secret" {
  length  = 32
  special = true
}

# Cloud SQL instance (optional, for metadata storage)
resource "google_sql_database_instance" "ai_overview_db" {
  name             = "ai-overview-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    
    backup_configuration {
      enabled = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = false

  depends_on = [google_project_service.required_apis]
}

resource "google_sql_database" "ai_overview_database" {
  name     = "ai_overview"
  instance = google_sql_database_instance.ai_overview_db.name
}

resource "google_sql_user" "ai_overview_user" {
  name     = "ai_overview_user"
  instance = google_sql_database_instance.ai_overview_db.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Cloud Scheduler jobs for automation
resource "google_cloud_scheduler_job" "daily_cleanup" {
  name             = "daily-cleanup"
  description      = "Daily cleanup of old temporary files"
  schedule         = "0 2 * * *"
  time_zone        = "UTC"
  attempt_deadline = "300s"

  pubsub_target {
    topic_name = google_pubsub_topic.ai_overview_pipeline.id
    data       = base64encode(jsonencode({
      step = "cleanup"
      type = "daily"
    }))
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Monitoring notification channel (email)
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notification"
  type         = "email"
  
  labels = {
    email_address = "admin@example.com"  # Replace with actual email
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Monitoring alert policies
resource "google_monitoring_alert_policy" "function_errors" {
  display_name = "Cloud Function Errors"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Function error rate"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_function\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "300s"
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  depends_on = [google_project_service.required_apis]
}

# Outputs
output "project_id" {
  description = "Project ID"
  value       = var.project_id
}

output "storage_bucket_name" {
  description = "Cloud Storage bucket name"
  value       = google_storage_bucket.ai_overview_data.name
}

output "pubsub_topic" {
  description = "PubSub topic name"
  value       = google_pubsub_topic.ai_overview_pipeline.name
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.ai_overview_db.connection_name
}

output "artifact_registry_repo" {
  description = "Artifact Registry repository"
  value       = google_artifact_registry_repository.ai_overview_repo.name
}

output "function_service_account" {
  description = "Cloud Functions service account email"
  value       = google_service_account.cloud_functions_sa.email
}

output "web_app_service_account" {
  description = "Web app service account email"
  value       = google_service_account.cloud_run_sa.email
} 
