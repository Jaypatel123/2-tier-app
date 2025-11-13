#!/bin/bash

# Push script for Docker images to Docker Hub
# Usage: ./push.sh [your-dockerhub-username] [version]

set -e  # Exit on error

DOCKERHUB_USERNAME=${1:-"your-username"}
VERSION=${2:-"latest"}
APP_IMAGE_NAME="flask-reels-app"
MYSQL_IMAGE_NAME="flask-reels-mysql"

if [ "$DOCKERHUB_USERNAME" == "your-username" ]; then
    echo "Error: Please provide your Docker Hub username"
    echo "Usage: ./push.sh <dockerhub-username> [version]"
    echo "Example: ./push.sh myusername v1.0.0"
    exit 1
fi

echo "=========================================="
echo "Pushing Docker images to Docker Hub..."
echo "Docker Hub Username: $DOCKERHUB_USERNAME"
echo "Version: $VERSION"
echo "=========================================="

# Check if user is logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    echo ""
    echo "Please login to Docker Hub..."
    docker login
fi

# Push Flask app image
echo ""
echo "Pushing Flask app image..."
echo "  Pushing $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:$VERSION..."
docker push $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:$VERSION

if [ "$VERSION" != "latest" ]; then
    echo "  Pushing $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:latest..."
    docker push $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:latest
fi

# Push MySQL image
echo ""
echo "Pushing MySQL image..."
echo "  Pushing $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:$VERSION..."
docker push $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:$VERSION

if [ "$VERSION" != "latest" ]; then
    echo "  Pushing $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:latest..."
    docker push $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:latest
fi

echo ""
echo "=========================================="
echo "Push complete!"
echo "=========================================="
echo ""
echo "Images available at:"
echo "  https://hub.docker.com/r/$DOCKERHUB_USERNAME/$APP_IMAGE_NAME"
echo "  https://hub.docker.com/r/$DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME"
echo ""
echo "To pull and run on AWS EC2:"
echo "  docker pull $DOCKERHUB_USERNAME/$APP_IMAGE_NAME:$VERSION"
echo "  docker pull $DOCKERHUB_USERNAME/$MYSQL_IMAGE_NAME:$VERSION"
echo ""

