# Docker Setup Guide

This guide explains how to build, push, and deploy the Flask Reels application using Docker.

## Prerequisites

- Docker installed on your machine
- Docker Hub account (for pushing images)
- Docker Compose installed

## Project Structure

- `Dockerfile` - Flask application image
- `Dockerfile.mysql` - Custom MySQL image with initialization
- `docker-compose.yml` - Local development setup
- `docker-compose.prod.yml` - Production setup for AWS EC2

## Building Docker Images

### Option 1: Using Build Script

1. Make the script executable:
```bash
chmod +x build.sh
```

2. Build images (replace `your-username` with your Docker Hub username):
```bash
./build.sh your-username
```

### Option 2: Manual Build

```bash
# Build Flask app image
docker build -t your-username/flask-reels-app:latest -f Dockerfile .

# Build MySQL image
docker build -t your-username/flask-reels-mysql:latest -f Dockerfile.mysql .
```

## Pushing to Docker Hub

### Option 1: Using Push Script

1. Make the script executable:
```bash
chmod +x push.sh
```

2. Push images:
```bash
./push.sh your-username
```

### Option 2: Manual Push

1. Login to Docker Hub:
```bash
docker login
```

2. Push images:
```bash
docker push your-username/flask-reels-app:latest
docker push your-username/flask-reels-mysql:latest
```

## Local Development

1. Create a `.env` file with your configuration:
```env
MYSQL_HOST=mysql
MYSQL_USER=reels_user
MYSQL_PASSWORD=your_password
MYSQL_DB=reels_db
MYSQL_ROOT_PASSWORD=root_password
SECRET_KEY=your-secret-key-here
```

2. Start services:
```bash
docker-compose up -d
```

3. Initialize database (first time only):
```bash
docker-compose exec app python init_db.py
```

4. Access the application:
- App: http://localhost:5001
- MySQL: localhost:3306

5. Stop services:
```bash
docker-compose down
```

## AWS EC2 Deployment

### Step 1: Prepare EC2 Instance

1. Launch an EC2 instance (Ubuntu 22.04 LTS recommended)
2. Install Docker and Docker Compose:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
# Logout and login again
```

### Step 2: Configure Environment

1. SSH into your EC2 instance
2. Create a directory for the app:
```bash
mkdir -p ~/reels-app
cd ~/reels-app
```

3. Create `.env` file:
```bash
nano .env
```

Add your configuration:
```env
DOCKERHUB_USERNAME=your-username
MYSQL_ROOT_PASSWORD=strong-root-password
MYSQL_USER=reels_user
MYSQL_PASSWORD=strong-user-password
MYSQL_DB=reels_db
SECRET_KEY=generate-a-strong-secret-key-here
```

4. Create `docker-compose.prod.yml` (or download from repo):
```bash
# Copy the docker-compose.prod.yml file to EC2
```

### Step 3: Deploy

1. Pull and start containers:
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

2. Check logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

3. Initialize database (first time only):
```bash
docker-compose -f docker-compose.prod.yml exec app python init_db.py
```

### Step 4: Configure Security Group

In AWS EC2 Console:
1. Go to Security Groups
2. Add inbound rule:
   - Type: Custom TCP
   - Port: 5001
   - Source: 0.0.0.0/0 (or your IP for security)

### Step 5: Access Application

Access your app at: `http://your-ec2-public-ip:5001`

## Environment Variables

### Required Variables

- `MYSQL_HOST` - MySQL hostname (use `mysql` in docker-compose)
- `MYSQL_USER` - MySQL username
- `MYSQL_PASSWORD` - MySQL password
- `MYSQL_DB` - Database name
- `SECRET_KEY` - Flask secret key for sessions

### Optional Variables

- `MYSQL_ROOT_PASSWORD` - MySQL root password
- `PORT` - Application port (default: 5001)
- `FLASK_ENV` - Flask environment (development/production)

## Troubleshooting

### Database Connection Issues

1. Check if MySQL container is healthy:
```bash
docker-compose ps
```

2. Check MySQL logs:
```bash
docker-compose logs mysql
```

3. Test connection:
```bash
docker-compose exec app python -c "import pymysql; pymysql.connect(host='mysql', user='reels_user', password='your_password', database='reels_db')"
```

### Application Not Starting

1. Check application logs:
```bash
docker-compose logs app
```

2. Check if port is available:
```bash
netstat -tuln | grep 5001
```

### Volume Mount Issues

Ensure the `static/reels` directory exists and has proper permissions:
```bash
mkdir -p static/reels
chmod -R 755 static/reels
```

## Updating Images

1. Rebuild images locally:
```bash
./build.sh your-username
```

2. Push to Docker Hub:
```bash
./push.sh your-username
```

3. On EC2, pull and restart:
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Backup Database

```bash
# Create backup
docker-compose exec mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} reels_db > backup.sql

# Restore backup
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} reels_db < backup.sql
```

## Notes

- The MySQL image uses the official MySQL 8.0 image with custom initialization
- The Flask app image is based on Python 3.11 slim
- Reels videos are mounted as volumes, so they persist across container restarts
- Database data is stored in a Docker volume for persistence

