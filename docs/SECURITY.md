# Security Best Practices and Guidelines

## Overview

This document outlines the comprehensive security measures, best practices, and procedures for the AI Company Platform infrastructure and secrets management.

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Secrets Management](#secrets-management)
3. [Infrastructure Security](#infrastructure-security)
4. [Secret Rotation](#secret-rotation)
5. [Access Control](#access-control)
6. [Compliance and Auditing](#compliance-and-auditing)
7. [Incident Response](#incident-response)

---

## Environment Configuration

### .env File Security

**Critical Rule**: Never commit `.env` files with actual secrets to version control.

#### Setup

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Update with actual values:

   ```bash
   # Do NOT use placeholder values in production
   DATABASE_PASSWORD=your_secure_password_here
   JWT_SECRET=generate_with_openssl_rand_base64_32
   ENCRYPTION_KEY=generate_with_openssl_rand_hex_32
   ```

3. Verify `.env` is in `.gitignore`:
   ```bash
   grep "^\.env$" .gitignore
   ```

#### Environment-Specific Files

- `.env.example` - Template with placeholders (SAFE TO COMMIT)
- `.env` - Local development (NEVER COMMIT)
- `.env.local` - Local overrides (NEVER COMMIT)
- `.env.*.local` - Environment-specific local (NEVER COMMIT)

### Required Environment Variables Validation

The application validates required environment variables on startup:

```javascript
// Example validation in your application
const requiredEnvVars = [
  "DATABASE_URL",
  "REDIS_URL",
  "JWT_SECRET",
  "ENCRYPTION_KEY",
  "NODE_ENV",
  "API_BASE_URL",
];

for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
}
```

---

## Secrets Management

### Hierarchy of Secrets Management

#### 1. Development Environment

**Location**: Local machine

```bash
# Copy from template
cp .env.example .env

# Generate secure secrets
openssl rand -base64 32  # For JWT_SECRET, SESSION_SECRET
openssl rand -hex 32     # For ENCRYPTION_KEY
```

**Tools**:

- `.env` files (local only)
- Environment variables (local)
- Password managers (LastPass, 1Password, Bitwarden)

#### 2. CI/CD Environment (GitHub Actions)

**Location**: GitHub Secrets

Use GitHub Secrets for all CI/CD pipeline credentials:

```bash
# Add secret via GitHub CLI
gh secret set DATABASE_PASSWORD --body "your-password"
gh secret set JWT_SECRET --body "$(openssl rand -base64 32)"
gh secret set ENCRYPTION_KEY --body "$(openssl rand -hex 32)"
```

**Reference in workflow**:

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        env:
          DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
          JWT_SECRET: ${{ secrets.JWT_SECRET }}
        run: |
          npm run deploy
```

#### 3. Staging Environment

**Location**: AWS Secrets Manager or Google Secret Manager

```bash
# Using AWS Secrets Manager
aws secretsmanager create-secret \
  --name ai-company-staging-secrets \
  --secret-string '{
    "DATABASE_PASSWORD": "...",
    "JWT_SECRET": "...",
    "ENCRYPTION_KEY": "..."
  }'
```

#### 4. Production Environment

**Location**: Managed Secret Store

Use one of:

- **Google Secret Manager** (for GCP deployments)
- **AWS Secrets Manager** (for AWS deployments)
- **HashiCorp Vault** (for multi-cloud)
- **Azure Key Vault** (for Azure deployments)

### Secret Types and Best Practices

#### Database Credentials

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
DATABASE_PASSWORD=<generate-32-char-random-string>
```

**Rotation**: Every 90 days or when employee leaves

#### API Keys

```env
OPENAI_API_KEY=sk-<random-alphanumeric>
ANTHROPIC_API_KEY=sk-ant-<random-alphanumeric>
GITHUB_TOKEN=ghp_<random-alphanumeric>
```

**Rotation**: Every 30 days

#### Encryption Keys

```env
JWT_SECRET=<base64-32-chars>
SESSION_SECRET=<base64-32-chars>
ENCRYPTION_KEY=<hex-64-chars>
```

**Rotation**: Every 180 days (plan for key versioning)

#### Tokens & Credentials

```env
SLACK_BOT_TOKEN=xoxb-<token>
STRIPE_SECRET_KEY=sk_live_<key>
```

**Rotation**: When compromised or on schedule

---

## Infrastructure Security

### Terraform Security

#### State File Protection

```hcl
# infrastructure/terraform/main.tf
terraform {
  backend "gcs" {
    bucket  = "your-terraform-state-bucket"
    prefix  = "terraform/state"
    encryption_key = "..."
  }
}
```

**Requirements**:

- Enable versioning on state bucket
- Enable encryption at rest
- Restrict access with IAM roles
- Enable audit logging
- Disable public access

#### Sensitive Variables

```hcl
# infrastructure/terraform/variables.tf
variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true  # Prevents logging
}
```

#### Managing Terraform Secrets

```bash
# Use .tfvars files (NEVER commit to git)
terraform plan -var-file="terraform.prod.tfvars"

# Add to .gitignore
echo "*.tfvars" >> .gitignore
echo "!example.tfvars" >> .gitignore
```

### Cloud SQL Security

```hcl
# infrastructure/terraform/main.tf
resource "google_sql_database_instance" "postgres" {
  # ...
  settings {
    ip_configuration {
      require_ssl                       = true
      private_network                   = google_compute_network.vpc.id
      authorized_networks {
        # Restrict to specific networks
        cidr = "10.0.0.0/8"
      }
    }
  }
}
```

**Best Practices**:

- Use SSL/TLS for all connections
- Use private networks when possible
- Enable Cloud SQL Proxy for secure connections
- Regular backups with point-in-time recovery
- Monitor access logs

### Kubernetes Secrets Security

#### Using External Secrets Operator

```yaml
# infrastructure/kubernetes/secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  secretStoreRef:
    name: gcpsm-secret-store
    kind: SecretStore
  target:
    name: app-secrets
  data:
    - secretKey: DATABASE_PASSWORD
      remoteRef:
        key: database-password
```

**Flow**:

1. Secrets stored in Google Secret Manager (never in etcd)
2. External Secrets Operator syncs to K8s Secrets
3. Pods mount secrets from K8s
4. Regular rotation triggers updates

#### Network Policies

```yaml
# infrastructure/kubernetes/namespace.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: production-network-policy
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  # Only allow ingress from ingress controller
  # Only allow egress to DNS and services
```

#### RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: app-role
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list", "watch"] # Never "create", "delete", "update"
```

---

## Secret Rotation

### Automated Rotation Script

Use the provided `scripts/rotate-secrets.sh`:

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

### Rotation Schedule

| Secret Type          | Rotation Frequency    | Trigger                           |
| -------------------- | --------------------- | --------------------------------- |
| Database Credentials | 90 days               | Scheduled + Employee Offboarding  |
| API Keys             | 30 days               | Scheduled + Suspected Compromise  |
| Encryption Keys      | 180 days              | Scheduled (plan key versioning)   |
| JWT Secret           | 180 days              | Scheduled + Suspected Compromise  |
| OAuth Tokens         | 30 days               | Scheduled + On Permission Changes |
| TLS Certificates     | 30 days before expiry | Automated                         |

### Rotation Procedure

1. **Planning Phase**
   - Notify teams of upcoming rotation
   - Schedule during low-traffic period
   - Ensure backup systems ready

2. **Execution Phase**

   ```bash
   # Backup current secrets
   cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

   # Run rotation script
   bash scripts/rotate-secrets.sh all

   # Update external systems (GitHub Secrets, Cloud KMS, etc.)
   gh secret set DATABASE_PASSWORD --body "new-password"
   ```

3. **Validation Phase**
   - Test database connectivity
   - Verify API keys work
   - Check application health
   - Monitor logs for errors

4. **Deployment Phase**
   - Deploy new secrets to production
   - Trigger pod restart in Kubernetes
   - Monitor for issues
   - Keep old secrets for fallback (24 hours)

5. **Cleanup Phase**
   - Confirm all systems working
   - Archive old secrets securely
   - Update documentation
   - Send completion notification

### Emergency Rotation

For compromised secrets:

```bash
# Immediate action
bash scripts/rotate-secrets.sh all

# Verify no unauthorized access
# Check audit logs for suspicious activity

# Force application restart
docker-compose restart
# or
kubectl rollout restart deployment/app-name

# Review and revoke compromised keys in external systems
# Follow incident response procedure
```

---

## Access Control

### GitHub Secrets Protection

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    name: Deploy to Production
    environment: production # Requires approval
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        env:
          DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
        run: npm run deploy
```

**Configuration**:

1. Create environment in GitHub Settings
2. Enable required reviewers
3. Restrict deployment branches
4. Use GitHub's built-in protection

### Kubernetes RBAC

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: app-role
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get"] # Minimal permissions
```

### Infrastructure Access

- **GCP**: Use Workload Identity for K8s to GCP access
- **AWS**: Use IRSA (IAM Roles for Service Accounts)
- **Azure**: Use Azure AD Workload Identity

```hcl
# infrastructure/terraform/main.tf
resource "google_service_account_iam_member" "workload_identity" {
  service_account_id = google_service_account.gke_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${data.google_client_config.default.project}.svc.id.goog[production/app-sa]"
}
```

---

## Compliance and Auditing

### Audit Logging

#### Cloud Logging (GCP)

```hcl
# infrastructure/terraform/main.tf
resource "google_sql_database_instance" "postgres" {
  settings {
    # Enable Cloud SQL audit logs
  }
}
```

#### Application Logging

```javascript
// Log all secret access attempts
logger.info("Accessing secret", {
  user: req.user.id,
  secret: "DATABASE_PASSWORD",
  timestamp: new Date().toISOString(),
  ip: req.ip,
});
```

### Compliance Standards

- **PCI DSS**: For payment processing
- **HIPAA**: For healthcare data
- **SOC 2**: For trusted service providers
- **GDPR**: For EU data
- **ISO 27001**: General information security

### Regular Security Reviews

**Quarterly**:

- Review access logs
- Check for unusual patterns
- Audit secret usage
- Verify rotation compliance

**Annually**:

- Full security assessment
- Penetration testing
- Compliance audit
- Disaster recovery drill

---

## Incident Response

### Suspected Secret Compromise

**Immediate Actions**:

1. Isolate affected systems
2. Begin audit log review
3. Notify security team
4. Prepare rotation plan

**Within 1 Hour**:

```bash
# Rotate compromised secrets immediately
bash scripts/rotate-secrets.sh all

# Force application restart
kubectl rollout restart deployment/app-name -n production

# Revoke old credentials in external systems
gh secret set COMPROMISED_KEY --body "revoked"
```

**Within 4 Hours**:

- Complete audit of suspicious access
- Notify affected customers if necessary
- Update incident log
- Begin root cause analysis

**Within 24 Hours**:

- Complete RCA document
- Implement preventive measures
- Brief stakeholders
- Close incident ticket

### Security Event Checklist

- [ ] Identify scope and impact
- [ ] Isolate affected systems
- [ ] Preserve evidence (logs, snapshots)
- [ ] Rotate all affected secrets
- [ ] Notify relevant teams
- [ ] Conduct investigation
- [ ] Document findings
- [ ] Implement improvements
- [ ] Brief stakeholders
- [ ] Schedule post-incident review

---

## Tools and Commands Reference

### Generate Secrets

```bash
# JWT Secret (base64)
openssl rand -base64 32

# Encryption Key (hex)
openssl rand -hex 32

# Secure Password (25 chars)
openssl rand -base64 32 | tr -d '/+=' | cut -c1-25

# GitHub Token simulation
openssl rand -hex 20
```

### Secret Management Tools

```bash
# Using direnv for local development
echo "export DATABASE_PASSWORD='your-password'" > .envrc
direnv allow

# Using chamber (AWS Secrets Manager)
chamber read prod DATABASE_PASSWORD

# Using Vault (HashiCorp)
vault kv get secret/production/database

# Using gcloud (Google Secret Manager)
gcloud secrets versions access latest --secret="database-password"
```

### Verification Commands

```bash
# Check if .env is properly gitignored
git check-ignore .env

# Scan for secrets in git history
truffleHog filesystem . --json

# Verify no hardcoded secrets
grep -r "password=" . --include="*.js" --include="*.ts"

# Check environment variables
env | grep -E "(SECRET|PASSWORD|KEY|TOKEN)"
```

---

## Additional Resources

- [OWASP Top 10 - A05:2021 Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [12 Factor App - Config](https://12factor.net/config)
- [Google Cloud - Secret Manager Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
- [AWS - Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

## Support and Questions

For security-related questions or to report vulnerabilities:

- Create a confidential issue in GitHub
- Contact security team: security@aicompany.com
- Do NOT commit sensitive information to any repository

Last Updated: 2025-11-08
Version: 1.0
