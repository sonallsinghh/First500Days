#!/bin/bash
# Deployment script for Azure App Service

set -e

RESOURCE_GROUP="agentic-rag-rg"
APP_NAME="agentic-rag-sonal"

echo "🚀 Starting deployment to Azure App Service..."

# Check app status
echo "📊 Checking app status..."
STATE=$(az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query "state" -o tsv)
USAGE_STATE=$(az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query "usageState" -o tsv)

echo "   State: $STATE"
echo "   Usage State: $USAGE_STATE"

if [ "$STATE" != "Running" ] || [ "$USAGE_STATE" != "Normal" ]; then
    echo "⚠️  App is not in Running state. Attempting to start..."
    az webapp start --resource-group $RESOURCE_GROUP --name $APP_NAME
    sleep 10
    
    # Check again
    STATE=$(az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query "state" -o tsv)
    if [ "$STATE" != "Running" ]; then
        echo "❌ App is still not running. Please wait for quota reset or check Azure Portal."
        exit 1
    fi
fi

# Create deployment package
echo "📦 Creating deployment package..."
rm -f app.zip
zip -r app.zip app/ requirements.txt faiss_index/ \
    -x "*/__pycache__/*" "*.pyc" "*/venv/*" ".git/*" "*/data/documents/*" \
    > /dev/null 2>&1

echo "✅ Package created: $(ls -lh app.zip | awk '{print $5}')"

# Deploy
echo "🚀 Deploying to Azure..."
az webapp deploy \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --src-path app.zip \
    --type zip \
    --async false

echo "✅ Deployment complete!"
echo "🌐 App URL: https://$APP_NAME.azurewebsites.net"

