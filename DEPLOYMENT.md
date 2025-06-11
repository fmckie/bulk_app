# Deployment Guide

This guide covers the complete deployment setup for the Kinobody Tracker application with Docker, Supabase, Redis, and DigitalOcean.

## Architecture Overview

- **Development**: Local Docker environment with hot reload
- **Production**: DigitalOcean App Platform with auto-scaling
- **Database**: Supabase (separate projects for dev/prod)
- **Caching**: Upstash Redis (separate instances for dev/prod)
- **CI/CD**: GitHub Actions with branch-based deployments

## Prerequisites

1. **Accounts Required**:
   - GitHub account
   - Supabase account (2 projects: dev & prod)
   - Upstash account (2 Redis databases: dev & prod)
   - DigitalOcean account with container registry

2. **Local Tools**:
   - Docker and Docker Compose
   - Python 3.11+
   - Git

## Initial Setup

### 1. Clone and Configure Repository

```bash
git clone <your-repo>
cd bulk_app

# Create development branch
git checkout -b dev

# Copy environment templates
cp .env.dev .env.dev.local
cp .env.prod .env.prod.local
```

### 2. Configure Supabase

1. Create two Supabase projects:
   - `kinobody-dev` for development
   - `kinobody-prod` for production

2. For each project:
   - Copy the project URL and anon key
   - Enable Email/Password authentication
   - Enable Google OAuth (optional)

3. Update environment files with Supabase credentials

### 3. Configure Upstash Redis

1. Create two Redis databases in Upstash:
   - `kinobody-dev` (closest region)
   - `kinobody-prod` (closest region)

2. For each database:
   - Copy the REST URL and token
   - Note the connection limits

3. Update environment files with Redis credentials

### 4. Configure DigitalOcean

1. Create a container registry in DigitalOcean
2. Create two App Platform apps:
   - `kinobody-tracker-dev`
   - `kinobody-tracker`

3. Note the app IDs for GitHub Actions

### 5. Set up GitHub Secrets

Add these secrets to your GitHub repository:

**Development Secrets**:
- `DEV_SUPABASE_URL`
- `DEV_SUPABASE_KEY`
- `DEV_UPSTASH_URL`
- `DEV_UPSTASH_TOKEN`
- `DEV_APP_ID`

**Production Secrets**:
- `PROD_SUPABASE_URL`
- `PROD_SUPABASE_KEY`
- `PROD_UPSTASH_URL`
- `PROD_UPSTASH_TOKEN`
- `PROD_APP_ID`
- `SENTRY_DSN`

**Shared Secrets**:
- `DIGITALOCEAN_ACCESS_TOKEN`
- `DIGITALOCEAN_REGISTRY`

## Development Workflow

### 1. Local Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Run with specific env file
docker-compose -f docker-compose.dev.yml --env-file .env.dev.local up

# Run tests
docker-compose -f docker-compose.dev.yml run web pytest

# Format code
docker-compose -f docker-compose.dev.yml run web black .
```

### 2. Database Migrations

```bash
# Create new migration
python scripts/setup_deployment.py development --create-migration

# Apply migrations to development
python scripts/setup_deployment.py development --component supabase

# Apply to production (usually done via CI/CD)
python scripts/setup_deployment.py production --component supabase
```

### 3. Feature Development

1. Create feature branch from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature
   ```

2. Develop and test locally

3. Push to feature branch:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature
   ```

4. Create PR to `dev` branch

## Deployment Process

### Development Deployment (Automatic)

1. Push to `dev` branch triggers CI/CD
2. Tests run automatically
3. Docker image built and pushed to registry
4. Deployed to DigitalOcean dev app
5. Migrations run automatically

### Production Deployment

1. Create PR from `dev` to `main`
2. Review and approve PR
3. Merge triggers production CI/CD
4. Additional security scans run
5. Deployed with zero-downtime rolling update

### Manual Deployment (Emergency)

```bash
# Build production image
docker build --target production -t kinobody-tracker:prod .

# Tag for registry
docker tag kinobody-tracker:prod registry.digitalocean.com/your-registry/kinobody-tracker:prod

# Push to registry
docker push registry.digitalocean.com/your-registry/kinobody-tracker:prod

# Deploy using doctl
doctl apps create-deployment <app-id>
```

## Monitoring and Maintenance

### Health Checks

- Development: http://localhost:8000/health
- Production: https://your-app.ondigitalocean.app/health

### Logs

```bash
# View local logs
docker-compose -f docker-compose.dev.yml logs -f web

# View DigitalOcean logs
doctl apps logs <app-id> --type=run
```

### Database Backup

Supabase automatically backs up your database. For additional backups:

```python
# Using Supabase MCP tools
mcp__supabase__create_backup({
    "project_id": "your-project-id",
    "name": "manual-backup-2024-01-06"
})
```

### Redis Cache Management

```python
# Clear all cache
from services.redis_cache import default_cache
default_cache.delete_pattern("*")

# Monitor cache usage
mcp__upstash__redis_database_get_stats({
    "id": "your-redis-id",
    "period": "1d",
    "type": "throughput"
})
```

## Rollback Procedures

### Application Rollback

```bash
# List deployments
doctl apps list-deployments <app-id>

# Rollback to previous deployment
doctl apps create-deployment <app-id> --rollback <deployment-id>
```

### Database Rollback

1. Identify the migration to rollback to
2. Restore Supabase backup
3. Re-run migrations from that point

## Security Considerations

1. **Secrets Management**:
   - Never commit `.env` files
   - Use GitHub secrets for CI/CD
   - Rotate keys regularly

2. **Database Security**:
   - Row Level Security enabled
   - SSL connections required
   - Regular security updates

3. **Application Security**:
   - HTTPS only in production
   - Rate limiting enabled
   - Input validation on all endpoints

## Troubleshooting

### Common Issues

1. **Docker build fails**:
   ```bash
   # Clear Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker-compose build --no-cache
   ```

2. **Database connection errors**:
   - Check Supabase project status
   - Verify credentials in env files
   - Check Row Level Security policies

3. **Redis connection errors**:
   - Verify Upstash credentials
   - Check usage limits
   - Fall back to local Redis in dev

4. **Deployment fails**:
   - Check GitHub Actions logs
   - Verify DigitalOcean app status
   - Check container registry access

### Support

- Create issues in GitHub repository
- Check Supabase status page
- Monitor DigitalOcean platform status