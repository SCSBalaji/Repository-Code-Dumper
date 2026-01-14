# Docker Setup Guide

This guide covers all Docker-related setup and configuration for the Repository Code Dumper application.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Compose Configuration](#docker-compose-configuration)
- [Building Images](#building-images)
- [Running Services](#running-services)
- [Managing Containers](#managing-containers)
- [Troubleshooting](#troubleshooting)
- [Production Configuration](#production-configuration)

## Prerequisites

### Install Docker

#### Ubuntu/Debian

```bash
# Update package index
sudo apt update

# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add your user to docker group (optional, avoids using sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
```

#### CentOS/RHEL

```bash
# Install required packages
sudo yum install -y yum-utils

# Add Docker repository
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
```

#### macOS

Download and install Docker Desktop from [Docker Hub](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)

#### Windows

Download and install Docker Desktop from [Docker Hub](https://hub.docker.com/editions/community/docker-ce-desktop-windows/)

### Install Docker Compose

Docker Compose is included with Docker Desktop on macOS and Windows. For Linux:

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Apply executable permissions
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/Repository-Code-Dumper.git
cd Repository-Code-Dumper

# Build and start all services
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Access the application:
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Docker Compose Configuration

### Default Configuration

The `docker-compose.yml` file defines two services:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: repo-dumper-backend
    ports:
      - "8000:8000"
    environment:
      - OUTPUT_DIR=/app/outputs
      - PYTHONUNBUFFERED=1
    volumes:
      - output_files:/app/outputs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      args:
        - REACT_APP_API_URL=
    container_name: repo-dumper-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  output_files:
    driver: local
```

### Service Details

#### Backend Service

- **Image**: Python 3.11 with FastAPI
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Volume**: Persists output files

#### Frontend Service

- **Image**: Node.js build + Nginx
- **Port**: 80
- **Proxies**: API requests to backend

## Building Images

### Build All Services

```bash
docker-compose build
```

### Build Specific Service

```bash
# Build only backend
docker-compose build backend

# Build only frontend
docker-compose build frontend
```

### Build with No Cache

```bash
docker-compose build --no-cache
```

### Build and Start

```bash
docker-compose up --build
```

## Running Services

### Start All Services

```bash
# Start in foreground (see logs)
docker-compose up

# Start in background (detached)
docker-compose up -d
```

### Start Specific Service

```bash
docker-compose up backend
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

## Managing Containers

### View Status

```bash
# List running containers
docker-compose ps

# List all containers (including stopped)
docker-compose ps -a
```

### View Logs

```bash
# All services
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Specific service
docker-compose logs backend

# Last N lines
docker-compose logs --tail=100 backend
```

### Execute Commands in Container

```bash
# Open shell in backend
docker-compose exec backend bash

# Run Python command
docker-compose exec backend python -c "print('Hello')"

# Run tests
docker-compose exec backend pytest
```

### Copy Files

```bash
# Copy from container to host
docker cp repo-dumper-backend:/app/outputs/file.md ./

# Copy from host to container
docker cp ./file.txt repo-dumper-backend:/app/
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Or use different ports
# Edit docker-compose.yml:
# ports:
#   - "8001:8000"
```

#### Container Won't Start

```bash
# Check logs for errors
docker-compose logs backend

# Check container status
docker-compose ps -a

# Try rebuilding
docker-compose build --no-cache backend
```

#### Permission Denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker-compose up
```

#### Out of Disk Space

```bash
# Clean up unused images
docker image prune -a

# Clean up everything unused
docker system prune -a

# Check disk usage
docker system df
```

### Debugging

```bash
# Check backend health
curl http://localhost:8000/health

# Check container resource usage
docker stats

# Inspect container
docker inspect repo-dumper-backend
```

## Production Configuration

### Create Production Override File

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    restart: always
    environment:
      - OUTPUT_DIR=/app/outputs
      - PYTHONUNBUFFERED=1
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  frontend:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
```

### Run in Production

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### With SSL (Using Traefik or nginx-proxy)

See [DEPLOYMENT.md](./DEPLOYMENT.md) for SSL setup instructions.

### Backup Output Files

```bash
# Create backup
docker-compose exec backend tar czf /tmp/backup.tar.gz /app/outputs
docker cp repo-dumper-backend:/tmp/backup.tar.gz ./backup.tar.gz

# Restore backup
docker cp ./backup.tar.gz repo-dumper-backend:/tmp/
docker-compose exec backend tar xzf /tmp/backup.tar.gz -C /
```

## Docker Images

### Building Custom Images

#### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

# Install git (required for cloning)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/outputs

ENV PYTHONUNBUFFERED=1
ENV OUTPUT_DIR=/app/outputs

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

```dockerfile
# Build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Pushing to Registry

```bash
# Tag images
docker tag repo-dumper-backend:latest yourusername/repo-dumper-backend:latest
docker tag repo-dumper-frontend:latest yourusername/repo-dumper-frontend:latest

# Push to Docker Hub
docker push yourusername/repo-dumper-backend:latest
docker push yourusername/repo-dumper-frontend:latest
```

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start services in background |
| `docker-compose down` | Stop and remove containers |
| `docker-compose logs -f` | Follow logs |
| `docker-compose ps` | List running services |
| `docker-compose build` | Build images |
| `docker-compose restart` | Restart all services |
| `docker-compose exec backend bash` | Open shell in container |
| `docker system prune -a` | Clean up unused resources |
