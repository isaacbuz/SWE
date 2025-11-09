# Secret Management

This directory contains secret management configuration and documentation.

## Overview

The platform uses a multi-layered secret management approach:

1. **GCP Secret Manager** (Production): Centralized secret storage
2. **External Secrets Operator** (Kubernetes): Syncs secrets from GCP to K8s
3. **Local Secrets** (Development): Environment variables and .env files

## Components

### GCP Secret Manager Integration

- **Module**: `packages/config/secrets.py`
- **Features**:
  - Secret creation and retrieval
  - Secret rotation
  - Version management
  - Access logging

### External Secrets Operator

- **Location**: `infrastructure/kubernetes/secrets/external-secrets-operator.yaml`
- **Purpose**: Syncs secrets from GCP Secret Manager to Kubernetes
- **Refresh Interval**: 1 hour

### Secret Rotation Script

- **Location**: `scripts/rotate-secrets.sh`
- **Features**:
  - Automated rotation
  - Backup before rotation
  - Validation after rotation
  - Multi-provider support

## Secret Types

### Database Credentials

- **Rotation**: Every 90 days
- **Secrets**: `database-url`, `database-password`

### API Keys

- **Rotation**: Every 30 days
- **Secrets**: `openai-api-key`, `anthropic-api-key`, `github-token`

### Encryption Keys

- **Rotation**: Every 180 days
- **Secrets**: `jwt-secret`, `session-secret`, `encryption-key`

### OAuth Tokens

- **Rotation**: Every 30 days or on permission changes
- **Secrets**: `github-token`, `slack-token`

## Usage

### Create Secret in GCP

```python
from packages.config.secrets import SecretManager, SecretType

manager = SecretManager()
await manager.create_secret(
    secret_id="database-password",
    secret_data="secure-password",
    secret_type=SecretType.DATABASE,
)
```

### Retrieve Secret

```python
from packages.config.secrets import get_secret

password = await get_secret("database-password")
```

### Rotate Secret

```python
from packages.config.secrets import rotate_secret

new_version = await rotate_secret("database-password")
```

### Rotate Secrets via Script

```bash
# Rotate all secrets
bash scripts/rotate-secrets.sh all

# Rotate only symmetric keys
bash scripts/rotate-secrets.sh symmetric

# Rotate only API keys
bash scripts/rotate-secrets.sh api-keys

# Rotate database credentials
bash scripts/rotate-secrets.sh database
```

## Kubernetes Integration

### External Secrets Operator Setup

1. Install External Secrets Operator:

```bash
kubectl apply -f https://raw.githubusercontent.com/external-secrets/external-secrets/main/deploy/charts/external-secrets/templates/crds/crds.yaml
```

2. Configure SecretStore:

```bash
kubectl apply -f infrastructure/kubernetes/secrets/external-secrets-operator.yaml
```

3. Secrets will be automatically synced to Kubernetes

### Using Secrets in Pods

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: api
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: DATABASE_URL
```

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use Secret Manager** for production secrets
3. **Rotate secrets regularly** according to schedule
4. **Limit access** to secrets using IAM roles
5. **Audit secret access** regularly
6. **Use separate secrets** for each environment
7. **Encrypt secrets at rest** (automatic with GCP Secret Manager)

## Development

### Local Development

For local development, use `.env` files:

```bash
cp .env.example .env
# Edit .env with your local secrets
```

The `LocalSecretManager` will automatically load from `.env`.

### Testing

```python
from packages.config.secrets import LocalSecretManager

manager = LocalSecretManager()
secret = await manager.get_secret("TEST_SECRET")
```

## Rotation Schedule

| Secret Type     | Frequency | Trigger                         |
| --------------- | --------- | ------------------------------- |
| Database        | 90 days   | Scheduled or offboarding        |
| API Keys        | 30 days   | Scheduled                       |
| JWT Secret      | 180 days  | Scheduled                       |
| Encryption Keys | 180 days  | Scheduled                       |
| TLS Certs       | Auto      | cert-manager                    |
| OAuth Tokens    | 30 days   | Scheduled or permission changes |

## Troubleshooting

### Secret Not Found

- Verify secret exists in GCP Secret Manager
- Check IAM permissions
- Verify secret ID spelling

### External Secrets Not Syncing

- Check External Secrets Operator logs
- Verify SecretStore configuration
- Check Workload Identity binding

### Rotation Failed

- Check backup was created
- Verify old secret still works
- Check logs for errors

## Documentation

- [Security Documentation](../../docs/SECURITY.md)
- [GCP Secret Manager Docs](https://cloud.google.com/secret-manager/docs)
- [External Secrets Operator Docs](https://external-secrets.io/)
