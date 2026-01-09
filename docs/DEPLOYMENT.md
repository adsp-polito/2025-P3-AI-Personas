# Deployment Guide

How to deploy the AI Personas system to production.

## Prerequisites

- Python 3.10+
- A server with at least 4GB RAM
- (Optional) Docker
- (Optional) Nginx for reverse proxy

## Deployment Options

### Option 1: Direct Python Deployment

**1. Clone and setup on server:**

```bash
git clone <repo-url>
cd 2025-P3-AI-Personas
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

**2. Configure environment:**

Create a `.env` file:

```bash
# LLM Backend
ADSP_LLM_BACKEND=openai
ADSP_LLM_BASE_URL=http://your-llm-service:8000/v1
ADSP_LLM_MODEL=your-model-name
ADSP_LLM_API_KEY=your-api-key

# API Server
ADSP_API_HOST=0.0.0.0
ADSP_API_PORT=8000
ADSP_API_LOG_LEVEL=info

# Context Filter (optional)
ADSP_CONTEXT_FILTER_ENABLED=true
ADSP_CONTEXT_FILTER_BACKEND=heuristic
```

**3. Run with systemd:**

Create `/etc/systemd/system/adsp-api.service`:

```ini
[Unit]
Description=AI Personas API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/2025-P3-AI-Personas
Environment="PATH=/opt/2025-P3-AI-Personas/venv/bin"
ExecStart=/opt/2025-P3-AI-Personas/venv/bin/python scripts/run_api.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable adsp-api
sudo systemctl start adsp-api
sudo systemctl status adsp-api
```

### Option 2: Docker Deployment

**1. Build the image:**

```bash
docker build -t adsp-api:latest .
```

**2. Run the container:**

```bash
docker run -d \
  --name adsp-api \
  -p 8000:8000 \
  -e ADSP_LLM_BASE_URL=http://your-llm:8000/v1 \
  -e ADSP_LLM_MODEL=your-model \
  -v $(pwd)/data:/app/data \
  adsp-api:latest
```

**3. Or use docker-compose:**

```bash
docker-compose up -d
```

### Option 3: Cloud Deployment

#### AWS EC2

1. Launch an EC2 instance (t3.medium or larger)
2. Configure security group to allow port 8000
3. SSH into instance and follow "Direct Python Deployment"
4. (Optional) Setup Elastic Load Balancer

#### Google Cloud Run

Cloud Run is suitable for stateless API deployments:

```bash
gcloud run deploy adsp-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Production Considerations

### Security

**1. Use HTTPS:**

Setup nginx as reverse proxy with SSL:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then use certbot for SSL:

```bash
sudo certbot --nginx -d yourdomain.com
```

**2. Environment variables:**

Never commit `.env` files. Use environment variables or secrets management:
- AWS Secrets Manager
- Google Secret Manager
- HashiCorp Vault

**3. Authentication:**

The built-in auth is basic. For production, consider:
- OAuth2/OIDC
- API keys with rate limiting
- JWT tokens

### Performance

**1. Run multiple workers:**

```bash
uvicorn adsp.app.api_server:create_app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

**2. Add caching:**

Enable the cache client in orchestrator config.

**3. Use a real vector database:**

Replace the in-memory vector DB with:
- Qdrant
- Pinecone
- Weaviate
- Milvus

### Monitoring

**1. Health checks:**

Setup automated health checks:

```bash
*/5 * * * * curl -f http://localhost:8000/health || alert
```

**2. Logging:**

Configure structured logging and ship logs to:
- CloudWatch (AWS)
- Cloud Logging (GCP)
- Elasticsearch + Kibana

**3. Metrics:**

Track:
- Request latency
- Error rates
- Token usage (if using paid LLM)

### Scaling

**Horizontal scaling:**

Run multiple API instances behind a load balancer. The in-memory components (memory, cache) won't be shared, so consider:

1. Use Redis for shared cache
2. Use PostgreSQL for conversation memory
3. Session affinity in load balancer

**Vertical scaling:**

If using large models locally:
- GPU instances for inference
- More RAM for larger context windows

## Database Migrations

When persona schemas change:

1. Backup existing data
2. Run migration scripts
3. Rebuild indexes
4. Test with sample queries

## Rollback Plan

Keep previous versions:

```bash
# Tag before deploying
git tag -a v1.0.0 -m "Production release"

# If issues occur, rollback
git checkout v0.9.0
./deploy.sh
```

## Checklist

Before going live:

- [ ] Environment variables configured
- [ ] HTTPS enabled
- [ ] Authentication working
- [ ] Health checks passing
- [ ] Logs being collected
- [ ] Backups configured
- [ ] Monitoring alerts setup
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on operations
