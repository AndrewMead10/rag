#!/bin/bash

# [SERVICE_NAME] Service Update Script
# This script updates the deployment with new changes
# Usage: ./update-deployment.sh [--full-rebuild]
# REPLACE [SERVICE_NAME] and [SERVICE_PORT] with actual values

set -e

SERVICE_NAME="your-service"  # REPLACE with actual service name
SERVICE_PORT="5000"          # REPLACE with actual port
FULL_REBUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full-rebuild)
            FULL_REBUILD=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--full-rebuild]"
            exit 1
            ;;
    esac
done

echo "Updating ${SERVICE_NAME} Service deployment..."

# Check if running in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found in current directory"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if service exists
if ! systemctl is-enabled "$SERVICE_NAME" &> /dev/null; then
    echo "Service $SERVICE_NAME is not set up. Please run setup-service.sh first."
    exit 1
fi

echo "Stopping the service..."
sudo systemctl stop "$SERVICE_NAME"

echo "Pulling latest changes (if this is a git repository)..."
if [ -d ".git" ]; then
    git pull origin $(git branch --show-current) || echo "No git repository or failed to pull"
fi

if [ "$FULL_REBUILD" = true ]; then
    echo "Full rebuild requested - rebuilding Docker image with no cache..."
    docker-compose build --no-cache
else
    echo "Quick update - rebuilding Docker image (using cache)..."
    docker-compose build
fi

echo "Removing old containers..."
docker-compose down --remove-orphans

echo "Starting updated service..."
sudo systemctl start "$SERVICE_NAME"

echo "Checking service status..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service is running successfully!"
    
    # Check if the API is responding
    if curl -s -f http://192.168.0.119:${SERVICE_PORT}/ > /dev/null; then
        echo "✅ API is responding at http://192.168.0.119:${SERVICE_PORT}"
    else
        echo "⚠️  Service is running but API may not be ready yet"
    fi
else
    echo "❌ Service failed to start"
    echo "Check service logs with: sudo systemctl status $SERVICE_NAME"
    exit 1
fi

echo ""
echo "Update complete!"
echo "Service logs: sudo journalctl -u $SERVICE_NAME -f"
echo "Docker logs: docker-compose logs -f"