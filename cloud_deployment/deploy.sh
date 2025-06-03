#!/bin/bash

# AI Overview Optimization - Cloud Deployment Script
# Tamamen cloud-based infrastructure'ı deploy eder

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="ai-overviews-v1"
REGION="us-central1"
ENVIRONMENT="dev"

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  AI OVERVIEW OPTIMIZATION - CLOUD DEPLOYMENT  ${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}🚀 $1${NC}"
    echo ""
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Check requirements
check_requirements() {
    print_step "Checking requirements..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud CLI not found. Please install it first."
        echo "https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Please install it first."
        echo "https://terraform.io/downloads"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install it first."
        echo "https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    print_success "All requirements satisfied"
}

# Get project configuration
get_project_config() {
    print_step "Getting project configuration..."
    
    if [ -z "$PROJECT_ID" ]; then
        # Try to get from gcloud config
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
        
        if [ -z "$PROJECT_ID" ]; then
            echo "Please enter your Google Cloud Project ID:"
            read -p "Project ID: " PROJECT_ID
        else
            echo "Using current gcloud project: $PROJECT_ID"
            read -p "Press Enter to continue or type a different project ID: " user_input
            if [ ! -z "$user_input" ]; then
                PROJECT_ID="$user_input"
            fi
        fi
    fi
    
    echo "Please select deployment region:"
    echo "1) us-central1 (default)"
    echo "2) europe-west1"
    echo "3) asia-east1"
    echo "4) Other (enter manually)"
    read -p "Choice [1]: " region_choice
    
    case $region_choice in
        2) REGION="europe-west1" ;;
        3) REGION="asia-east1" ;;
        4) 
            read -p "Enter region: " REGION
            ;;
        *) REGION="us-central1" ;;
    esac
    
    echo "Please select environment:"
    echo "1) dev (default)"
    echo "2) staging"
    echo "3) prod"
    read -p "Choice [1]: " env_choice
    
    case $env_choice in
        2) ENVIRONMENT="staging" ;;
        3) ENVIRONMENT="prod" ;;
        *) ENVIRONMENT="dev" ;;
    esac
    
    echo ""
    echo "Configuration:"
    echo "  Project ID: $PROJECT_ID"
    echo "  Region: $REGION"
    echo "  Environment: $ENVIRONMENT"
    echo ""
    read -p "Continue with this configuration? [Y/n]: " confirm
    
    if [[ $confirm =~ ^[Nn]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
}

# Setup gcloud authentication
setup_gcloud() {
    print_step "Setting up Google Cloud authentication..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_warning "Not authenticated. Starting authentication flow..."
        gcloud auth login
    fi
    
    # Enable application default credentials
    if [ ! -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
        print_warning "Setting up application default credentials..."
        gcloud auth application-default login
    fi
    
    print_success "Google Cloud authentication setup complete"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_step "Deploying infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    terraform init
    
    # Create terraform.tfvars
    cat > terraform.tfvars <<EOF
project_id  = "$PROJECT_ID"
region      = "$REGION"
environment = "$ENVIRONMENT"
EOF
    
    # Plan deployment
    echo "Reviewing Terraform plan..."
    terraform plan -var-file=terraform.tfvars
    
    echo ""
    read -p "Apply this Terraform plan? [Y/n]: " apply_confirm
    
    if [[ $apply_confirm =~ ^[Nn]$ ]]; then
        print_warning "Infrastructure deployment skipped."
        cd ..
        return
    fi
    
    # Apply deployment
    terraform apply -var-file=terraform.tfvars -auto-approve
    
    # Get outputs
    BUCKET_NAME=$(terraform output -raw storage_bucket_name)
    PUBSUB_TOPIC=$(terraform output -raw pubsub_topic)
    FUNCTION_SA=$(terraform output -raw function_service_account)
    WEB_APP_SA=$(terraform output -raw web_app_service_account)
    
    print_success "Infrastructure deployment complete"
    cd ..
}

# Build and deploy Cloud Functions
deploy_functions() {
    print_step "Deploying Cloud Functions..."
    
    cd functions
    
    # Deploy extract function
    print_step "Deploying extract-website-data function..."
    cd extract_website_data
    
    gcloud functions deploy extract-website-data \
        --gen2 \
        --runtime=python311 \
        --region=$REGION \
        --source=. \
        --entry-point=extract_website_data \
        --trigger=http \
        --timeout=540s \
        --memory=1GB \
        --service-account=$FUNCTION_SA \
        --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,STORAGE_BUCKET_NAME=$BUCKET_NAME,PUBSUB_TOPIC=$PUBSUB_TOPIC" \
        --allow-unauthenticated
    
    EXTRACT_URL=$(gcloud functions describe extract-website-data --region=$REGION --format="value(serviceConfig.uri)")
    cd ..
    
    # Deploy process batches function
    print_step "Deploying process-batches function..."
    cd process_batches
    
    gcloud functions deploy process-batches \
        --gen2 \
        --runtime=python311 \
        --region=$REGION \
        --source=. \
        --entry-point=process_batches \
        --trigger=http \
        --timeout=540s \
        --memory=1GB \
        --service-account=$FUNCTION_SA \
        --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,STORAGE_BUCKET_NAME=$BUCKET_NAME,PUBSUB_TOPIC=$PUBSUB_TOPIC" \
        --allow-unauthenticated
    
    PROCESS_URL=$(gcloud functions describe process-batches --region=$REGION --format="value(serviceConfig.uri)")
    cd ..
    
    # Deploy additional functions here...
    
    print_success "Cloud Functions deployment complete"
    cd ..
}

# Build and deploy web application
deploy_web_app() {
    print_step "Deploying web application to Cloud Run..."
    
    cd web_app
    
    # Create Dockerfile if not exists
    if [ ! -f "Dockerfile" ]; then
        cat > Dockerfile <<EOF
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "app.py"]
EOF
    fi
    
    # Create requirements.txt for web app
    if [ ! -f "requirements.txt" ]; then
        cat > requirements.txt <<EOF
Flask==2.3.3
google-cloud-storage==2.14.0
google-cloud-pubsub==2.21.1
google-cloud-sql-connector==0.11.0
google-cloud-discoveryengine==0.11.16
requests==2.31.0
gunicorn==21.2.0
EOF
    fi
    
    # Build and deploy to Cloud Run
    gcloud run deploy ai-overview-web-app \
        --source=. \
        --platform=managed \
        --region=$REGION \
        --service-account=$WEB_APP_SA \
        --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,STORAGE_BUCKET_NAME=$BUCKET_NAME,PUBSUB_TOPIC=$PUBSUB_TOPIC,EXTRACT_FUNCTION_URL=$EXTRACT_URL,PROCESS_FUNCTION_URL=$PROCESS_URL" \
        --allow-unauthenticated \
        --memory=1Gi \
        --timeout=300
    
    WEB_APP_URL=$(gcloud run services describe ai-overview-web-app --region=$REGION --format="value(status.url)")
    
    print_success "Web application deployment complete"
    cd ..
}

# Setup monitoring and alerts
setup_monitoring() {
    print_step "Setting up monitoring and alerts..."
    
    # Enable monitoring APIs (already done in Terraform)
    print_success "Monitoring setup complete"
}

# Verify deployment
verify_deployment() {
    print_step "Verifying deployment..."
    
    # Test web app
    if [ ! -z "$WEB_APP_URL" ]; then
        echo "Testing web application..."
        if curl -s -o /dev/null -w "%{http_code}" "$WEB_APP_URL/health" | grep -q "200"; then
            print_success "Web application is responding"
        else
            print_warning "Web application may not be ready yet"
        fi
    fi
    
    # Test extract function
    if [ ! -z "$EXTRACT_URL" ]; then
        echo "Testing extract function..."
        if curl -s -o /dev/null -w "%{http_code}" "$EXTRACT_URL" | grep -q "405\|200"; then
            print_success "Extract function is responding"
        else
            print_warning "Extract function may not be ready yet"
        fi
    fi
    
    print_success "Deployment verification complete"
}

# Cleanup function
cleanup() {
    echo ""
    print_step "Cleaning up temporary files..."
    # Add cleanup logic here if needed
}

# Main deployment flow
main() {
    print_header
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    check_requirements
    get_project_config
    setup_gcloud
    deploy_infrastructure
    deploy_functions
    deploy_web_app
    setup_monitoring
    verify_deployment
    
    echo ""
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE! 🎉${NC}"
    echo ""
    echo "=== DEPLOYMENT SUMMARY ==="
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Environment: $ENVIRONMENT"
    echo ""
    echo "=== ACCESS URLS ==="
    if [ ! -z "$WEB_APP_URL" ]; then
        echo "🌐 Web Application: $WEB_APP_URL"
    fi
    if [ ! -z "$EXTRACT_URL" ]; then
        echo "🔧 Extract Function: $EXTRACT_URL"
    fi
    if [ ! -z "$PROCESS_URL" ]; then
        echo "⚙️  Process Function: $PROCESS_URL"
    fi
    echo ""
    echo "=== NEXT STEPS ==="
    echo "1. Visit the web application to start your first AI Overview analysis"
    echo "2. Check Google Cloud Console for monitoring and logs"
    echo "3. Configure any additional settings as needed"
    echo ""
    echo "Happy analyzing! 🚀"
}

# Check if script is being sourced or executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 