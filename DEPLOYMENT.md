# ContextProvider Docker Deployment Guide

This guide covers deploying ContextProvider using Docker Compose on AWS EC2 or any Linux server.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   PostgreSQL    │
│   (React+Nginx) │◄──►│   (FastAPI)     │◄──►│   Database      │
│   Port: 80      │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   ChromaDB      │
                    │   Vector Store  │
                    │   Port: 8001    │
                    └─────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- AWS EC2 instance (t3.medium or larger recommended)
- Docker and Docker Compose installed
- Domain name (optional, for production)

### 2. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply group changes
```

### 3. Deploy Application

```bash
# Clone repository
git clone https://github.com/Jasuni69/ContextProvider.git
cd ContextProvider

# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
1. Check prerequisites
2. Setup environment files
3. Build Docker images
4. Start all services
5. Run database migrations
6. Display service URLs

## 🔧 Configuration

### Environment Variables

Copy `.env.production` to `.env` and update these values:

```bash
# Required - Update these values
POSTGRES_PASSWORD=your_secure_password_here
JWT_SECRET_KEY=your_jwt_secret_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Update for production
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ORIGINS=http://localhost,https://your-domain.com
```

### Google OAuth Setup

You'll need to configure Google OAuth credentials in your `.env` file:
- `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret

To get these credentials:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Create OAuth 2.0 credentials
5. Add your domain to authorized origins

## 📋 Service Management

### Start Services
```bash
./deploy.sh
```

### Stop Services
```bash
./deploy.sh stop
```

### Restart Services
```bash
./deploy.sh restart
```

### View Logs
```bash
./deploy.sh logs
```

### Clean Up (Remove all data)
```bash
./deploy.sh clean
```

## 🔍 Health Checks

### Frontend Health
```bash
curl http://localhost/health
```

### Backend Health
```bash
curl http://localhost:8000/health
```

### ChromaDB Health
```bash
curl http://localhost:8001/api/v1/heartbeat
```

### PostgreSQL Health
```bash
docker-compose exec postgres pg_isready -U contextuser -d contextprovider
```

## 📊 Service URLs

- **Frontend**: http://localhost (or your domain)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **ChromaDB**: http://localhost:8001

## 🛠️ Troubleshooting

### Check Service Status
```bash
docker-compose ps
```

### View Service Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs chromadb
```

### Access Service Shell
```bash
# Backend shell
docker-compose exec backend bash

# PostgreSQL shell
docker-compose exec postgres psql -U contextuser -d contextprovider
```

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   sudo netstat -tulpn | grep :80
   sudo netstat -tulpn | grep :8000
   
   # Stop conflicting services
   sudo systemctl stop apache2
   sudo systemctl stop nginx
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL logs
   docker-compose logs postgres
   
   # Test connection
   docker-compose exec postgres pg_isready -U contextuser
   ```

3. **ChromaDB Not Starting**
   ```bash
   # Check ChromaDB logs
   docker-compose logs chromadb
   
   # Test connection
   curl http://localhost:8001/api/v1/heartbeat
   ```

## 🔒 Security Considerations

### For Production Deployment

1. **Use HTTPS**
   - Configure SSL certificates
   - Use Let's Encrypt for free certificates

2. **Secure Database**
   - Use strong passwords
   - Limit database access
   - Enable connection encryption

3. **Environment Variables**
   - Never commit `.env` files
   - Use secure secret keys
   - Rotate API keys regularly

4. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

## 📈 Performance Optimization

### Resource Allocation

For production, consider these instance types:
- **Small**: t3.medium (2 vCPU, 4GB RAM)
- **Medium**: t3.large (2 vCPU, 8GB RAM)
- **Large**: t3.xlarge (4 vCPU, 16GB RAM)

### Database Optimization

```bash
# Increase PostgreSQL performance
docker-compose exec postgres psql -U contextuser -d contextprovider -c "
  ALTER SYSTEM SET shared_buffers = '256MB';
  ALTER SYSTEM SET effective_cache_size = '1GB';
  ALTER SYSTEM SET maintenance_work_mem = '64MB';
  SELECT pg_reload_conf();
"
```

## 🔄 Backup and Recovery

### Database Backup
```bash
# Create backup
docker-compose exec postgres pg_dump -U contextuser contextprovider > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U contextuser contextprovider < backup.sql
```

### Volume Backup
```bash
# Backup volumes
docker run --rm -v contextprovider_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
docker run --rm -v contextprovider_chroma_data:/data -v $(pwd):/backup alpine tar czf /backup/chroma_backup.tar.gz -C /data .
```

## 📞 Support

For issues or questions:
1. Check the logs first
2. Review this troubleshooting guide
3. Check GitHub issues
4. Create a new issue with logs and configuration details

## 🎯 Next Steps

1. **Domain Setup**: Configure your domain to point to the server
2. **SSL Certificate**: Set up HTTPS with Let's Encrypt
3. **Monitoring**: Add application monitoring
4. **Backups**: Set up automated backups
5. **CI/CD**: Configure automated deployments 