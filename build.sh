#!/bin/bash

# Build script for Docker images
# Usage: ./build.sh [your-dockerhub-username] [version]

set -e  # Exit on error

DOCKERHUB_USERNAME=${1:-"jaypatel97043"}
VERSION=${2:-"latest"}
APP_IMAGE_NAME="flask-reels-app"
MYSQL_IMAGE_NAME="flask-reels-mysql"

if [ "$DOCKERHUB_USERNAME" == "your-username" ]; then
    echo "Error: Please provide your Docker Hub username"
    echo "Usage: ./build.sh <dockerhub-username> [version]"
    echo "Example: ./build.sh myusername v1.0.0"
    exit 1
fi

echo "=========================================="
echo "Building Docker images..."
echo "Docker Hub Username: $DOCKERHUB_USERNAME"
echo "Version: $VERSION"
echo "=========================================="

# Build Flask app image
echo ""
echo "Building Flask app image..."
docker build -t $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:$VERSION \
             -t $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:latest \
             -f Dockerfile .

# Build MySQL image with init script
echo ""
echo "Building MySQL image with init script..."
docker build -t $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:$VERSION \
             -t $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:latest \
             -f Dockerfile.mysql .

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="
echo ""
echo "Images built:"
echo "  - $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:$VERSION"
echo "  - $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:latest"
echo "  - $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:$VERSION"
echo "  - $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:latest"
echo ""
echo "To push to Docker Hub, run:"
echo "  ./push.sh $DOCKERHUB_USERNAME $VERSION"
echo ""

