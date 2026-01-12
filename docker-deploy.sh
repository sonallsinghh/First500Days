#!/bin/bash
# Docker deployment script for Azure App Service

set -e

RESOURCE_GROUP="agentic-rag-rg"
APP_NAME="agentic-rag-sonal"
ACR_NAME="agenticragacr$(date +%s | tail -c 6)"  # Unique name
IMAGE_NAME="agentic-rag-app"
IMAGE_TAG="latest"

echo "🐳 Setting up Docker deployment..."

# Check if ACR exists, if not create one
echo "📦 Checking for Azure Container Registry..."
ACR_EXISTS=$(az acr list --resource-group $RESOURCE_GROUP --query "[?name=='$ACR_NAME'].name" -o tsv)

if [ -z "$ACR_EXISTS" ]; then
    echo "Creating Azure Container Registry..."
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true \
        --output none
    
    echo "✅ ACR created: $ACR_NAME"
else
    echo "✅ Using existing ACR: $ACR_NAME"
fi

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
FULL_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

echo "🔨 Building Docker image in Azure (cloud build - no local Docker needed)..."
# Build and push to ACR (builds in Azure cloud, no local Docker required)
az acr build \
    --registry $ACR_NAME \
    --image $IMAGE_NAME:$IMAGE_TAG \
    --file Dockerfile \
    .

echo "🚀 Configuring web app to use container..."
# Configure web app to use the container
az webapp config container set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --docker-custom-image-name $FULL_IMAGE_NAME \
    --docker-registry-server-url https://$ACR_LOGIN_SERVER \
    --docker-registry-server-user $(az acr credential show --name $ACR_NAME --query username -o tsv) \
    --docker-registry-server-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

echo "🔄 Restarting web app..."
az webapp restart --resource-group $RESOURCE_GROUP --name $APP_NAME

echo "✅ Deployment complete!"
echo "🌐 App URL: https://$APP_NAME.azurewebsites.net"
echo "📦 Container: $FULL_IMAGE_NAME"

