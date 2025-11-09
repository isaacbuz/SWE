# Runbook: Server Failure

## Overview

This runbook covers the procedure for recovering from complete server failure.

## Symptoms

- Server unreachable (ping fails)
- SSH connection refused
- All services down
- No response from infrastructure

## Prerequisites

- Infrastructure as Code (Terraform)
- Database backups available
- Container registry access
- DNS access

## Recovery Procedure

### Step 1: Assess Damage

```bash
# Check server status
ping <server-ip>

# Check DNS
dig <domain-name>

# Check cloud provider status
# (AWS/GCP/Azure console)
```

### Step 2: Provision New Infrastructure

```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan infrastructure
terraform plan -var-file="terraform.prod.tfvars"

# Apply infrastructure
terraform apply -var-file="terraform.prod.tfvars"
```

### Step 3: Restore Database

```bash
# Download latest backup from S3/GCS
aws s3 cp s3://swe-platform-backups/postgresql-backups/latest.sql.gz /tmp/

# Restore database
./scripts/db/restore-database.sh /tmp/latest.sql.gz
```

### Step 4: Deploy Application

```bash
# Pull Docker images
docker-compose pull

# Start services
docker-compose up -d

# Verify services
docker-compose ps
```

### Step 5: Restore Configuration

```bash
# Clone repository
git clone <repository-url>
cd swe-platform

# Restore environment variables
cp .env.example .env
# Edit .env with production values

# Restore secrets
# (from secret management system)
```

### Step 6: Verify Services

```bash
# Check API health
curl http://localhost:8000/health

# Check database connectivity
psql -h localhost -U swe_user -d swe_db -c "SELECT 1;"

# Check all services
docker-compose ps
```

### Step 7: Update DNS

```bash
# Update DNS records to point to new server
# (via DNS provider console or API)
```

## Verification

- [ ] Infrastructure provisioned
- [ ] Database restored
- [ ] Application deployed
- [ ] Services running
- [ ] DNS updated
- [ ] Health checks passing

## Post-Recovery

1. Document incident
2. Investigate root cause
3. Review infrastructure resilience
4. Update disaster recovery plan
5. Schedule post-mortem

## Related Scripts

- `scripts/dr/full-system-recovery.sh`
- `scripts/db/restore-database.sh`

