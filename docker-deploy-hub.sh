#!/bin/bash
# Docker deployment using Docker Hub (FREE)

set -e

RESOURCE_GROUP="agentic-rag-rg"
APP_NAME="agentic-rag-sonal"
DOCKER_HUB_USERNAME="${DOCKER_HUB_USERNAME:-your-dockerhub-username}"  # Set this or export
IMAGE_NAME="agentic-rag-app"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$DOCKER_HUB_USERNAME/$IMAGE_NAME:$IMAGE_TAG"

echo "🐳 Docker Hub Deployment"
echo "📦 Image: $FULL_IMAGE_NAME"

if [ "$DOCKER_HUB_USERNAME" = "your-dockerhub-username" ]; then
    echo "❌ Please set DOCKER_HUB_USERNAME environment variable"
    echo "   export DOCKER_HUB_USERNAME=your-username"
    exit 1
fi

echo "🔨 Building Docker image..."
docker build -t $FULL_IMAGE_NAME .

echo "📤 Pushing to Docker Hub..."
echo "   (You'll need to login: docker login)"
docker push $FULL_IMAGE_NAME

echo "🚀 Configuring Azure Web App..."
az webapp config container set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --docker-custom-image-name $FULL_IMAGE_NAME \
    --docker-registry-server-url https://index.docker.io/v1 \
    --docker-registry-server-user $DOCKER_HUB_USERNAME \
    --docker-registry-server-password $(echo "Enter Docker Hub password:" && read -s DOCKER_PASSWORD && echo $DOCKER_PASSWORD)

echo "🔄 Restarting web app..."
az webapp restart --resource-group $RESOURCE_GROUP --name $APP_NAME

echo "✅ Deployment complete!"
echo "🌐 App URL: https://$APP_NAME.azurewebsites.net"

