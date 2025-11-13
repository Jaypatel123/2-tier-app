# Docker Deployment Guide

This guide explains how to build, push, and deploy the Flask Reels application using Docker.

## Prerequisites

- Docker installed on your machine
- Docker Hub account
- AWS EC2 instance (for deployment)

## Quick Start

### 1. Build Docker Images

```bash
# Make scripts executable
chmod +x build.sh push.sh

# Build images (replace 'your-username' with your Docker Hub username)
./build.sh your-username v1.0.0
```

### 2. Push to Docker Hub

```bash
# Push images to Docker Hub
./push.sh your-username v1.0.0
```

You'll be prompted to login to Docker Hub if not already logged in.

### 3. Deploy on AWS EC2

#### Step 1: Connect to EC2 Instance

```bash
ssh -i your-key.pem ec2-user@your-ec2-ip
```

#### Step 2: Install Docker on EC2

```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install docker -y

# Start Docker service
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes to take effect
```

#### Step 3: Create Deployment Directory

```bash
mkdir -p ~/reels-app
cd ~/reels-app
```

#### Step 4: Create Environment File

```bash
cat > .env << EOF
DOCKERHUB_USERNAME=your-username
MYSQL_ROOT_PASSWORD=your-secure-root-password
MYSQL_USER=reels_user
MYSQL_PASSWORD=your-secure-password
MYSQL_DB=reels_db
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

#### Step 5: Create docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mysql:
    image: ${DOCKERHUB_USERNAME}/flask-reels-mysql:latest
    container_name: reels_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DB}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - reels_network

  app:
    image: ${DOCKERHUB_USERNAME}/flask-reels-app:latest
    container_name: reels_app
    restart: unless-stopped
    ports:
      - "5001:5001"
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_DB: ${MYSQL_DB}
      SECRET_KEY: ${SECRET_KEY}
      FLASK_ENV: production
    depends_on:
      mysql:
        condition: service_healthy
    volumes:
      - ./static/reels:/app/static/reels
    networks:
      - reels_network

volumes:
  mysql_data:

networks:
  reels_network:
    driver: bridge
EOF
```

#### Step 6: Create Reels Directory

```bash
mkdir -p static/reels
# Upload your video files to static/reels/ if needed
```

#### Step 7: Pull and Run Containers

```bash
# Pull images from Docker Hub
docker-compose pull

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### Step 8: Configure Security Group

In AWS EC2 Console:
1. Go to Security Groups
2. Edit inbound rules
3. Add rule:
   - Type: Custom TCP
   - Port: 5001
   - Source: 0.0.0.0/0 (or your IP for security)

#### Step 9: Access Application

Open your browser and navigate to:
```
http://your-ec2-public-ip:5001
```

## Manual Commands

### Build Images Manually

```bash
# Build Flask app
docker build -t your-username/flask-reels-app:latest -f Dockerfile .

# Build MySQL
docker build -t your-username/flask-reels-mysql:latest -f Dockerfile.mysql .
```

### Push Images Manually

```bash
# Login to Docker Hub
docker login

# Push Flask app
docker push your-username/flask-reels-app:latest

# Push MySQL
docker push your-username/flask-reels-mysql:latest
```

### Pull and Run on EC2

```bash
# Pull images
docker pull your-username/flask-reels-app:latest
docker pull your-username/flask-reels-mysql:latest

# Run MySQL
docker run -d \
  --name reels_mysql \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=reels_db \
  -e MYSQL_USER=reels_user \
  -e MYSQL_PASSWORD=reels_password \
  -p 3306:3306 \
  -v mysql_data:/var/lib/mysql \
  your-username/flask-reels-mysql:latest

# Run Flask app
docker run -d \
  --name reels_app \
  --link reels_mysql:mysql \
  -e MYSQL_HOST=mysql \
  -e MYSQL_USER=reels_user \
  -e MYSQL_PASSWORD=reels_password \
  -e MYSQL_DB=reels_db \
  -e SECRET_KEY=your-secret-key \
  -p 5001:5001 \
  -v $(pwd)/static/reels:/app/static/reels \
  your-username/flask-reels-app:latest
```

## Troubleshooting

### Check Container Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs app
docker-compose logs mysql

# Follow logs in real-time
docker-compose logs -f app
```

### Check Container Status

```bash
docker-compose ps
docker ps -a
```

### Restart Services

```bash
docker-compose restart
# or
docker-compose down
docker-compose up -d
```

### Access MySQL Container

```bash
docker exec -it reels_mysql mysql -u root -p
```

### Access Flask App Container

```bash
docker exec -it reels_app bash
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes database data)
docker-compose down -v

# Remove images
docker rmi your-username/flask-reels-app:latest
docker rmi your-username/flask-reels-mysql:latest
```

## Production Considerations

1. **Use Environment Variables**: Never hardcode passwords or secrets
2. **Use SSL/TLS**: Set up reverse proxy (nginx) with SSL certificates
3. **Backup Database**: Regularly backup MySQL data volumes
4. **Monitor Logs**: Set up log aggregation and monitoring
5. **Resource Limits**: Add resource limits to docker-compose.yml
6. **Health Checks**: Already configured in docker-compose.yml
7. **Auto-restart**: Containers are set to restart unless stopped

## Example with Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Support

For issues or questions, check:
- Container logs: `docker-compose logs`
- Application logs: Check Flask output
- MySQL logs: `docker-compose logs mysql`

