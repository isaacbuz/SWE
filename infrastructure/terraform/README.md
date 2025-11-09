# Terraform Infrastructure for PieHr Platform

This directory contains Terraform configurations for provisioning GCP infrastructure for the PieHr AI-First Software Engineering Platform.

## Structure

```
infrastructure/terraform/
├── main.tf                    # Main infrastructure resources
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output values
├── versions.tf                # Terraform and provider versions
├── modules/                   # Reusable modules (optional)
│   ├── gke/
│   ├── cloud-sql/
│   ├── redis/
│   ├── networking/
│   └── storage/
├── environments/              # Environment-specific configurations
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── backend.tf
└── README.md                  # This file
```

## Resources Provisioned

### Compute
- **GKE Cluster**: Kubernetes cluster with node pools
  - Default node pool (non-preemptible)
  - Spot node pool (preemptible, cost optimization)
  - Auto-scaling enabled
  - Network policies enabled
  - Workload Identity enabled

### Database
- **Cloud SQL PostgreSQL**: Managed PostgreSQL instance
  - Automated backups
  - Point-in-time recovery (production)
  - High availability (production)
  - Private IP access

### Cache
- **Cloud Memorystore Redis**: Managed Redis instance
  - Authentication enabled
  - Transit encryption (production)
  - Persistence enabled (production)
  - Private service access

### Storage
- **Cloud Storage Buckets**: For application artifacts and logs
  - Versioning enabled (production)
  - Lifecycle policies (90 days → Coldline, 365 days → Archive)
  - KMS encryption

### Networking
- **VPC Network**: Custom VPC with subnets
- **Private VPC Connection**: For Cloud SQL and Redis
- **Cloud DNS**: Managed DNS zone with records
- **Global Load Balancer IP**: External IP address

### Security
- **Cloud Armor**: Security policies
  - Rate limiting
  - IP blocking
  - DDoS protection
- **KMS**: Encryption keys for storage
- **IAM**: Service accounts and roles

### Monitoring
- **Cloud Monitoring**: Alert policies
- **Cloud Logging**: Centralized logging
- **Notification Channels**: Email alerts

## Prerequisites

1. **GCP Project**: Create a GCP project
2. **Billing**: Enable billing on the project
3. **APIs**: Enable required APIs:
   ```bash
   gcloud services enable \
     container.googleapis.com \
     sqladmin.googleapis.com \
     redis.googleapis.com \
     storage.googleapis.com \
     dns.googleapis.com \
     compute.googleapis.com \
     monitoring.googleapis.com \
     logging.googleapis.com
   ```
4. **Service Account**: Create service account with required permissions
5. **Terraform**: Install Terraform >= 1.5
6. **GCS Bucket**: Create GCS bucket for Terraform state (optional but recommended)

## Usage

### Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### Plan Infrastructure

```bash
# Staging
cd environments/staging
terraform init
terraform plan

# Production
cd environments/production
terraform init
terraform plan
```

### Apply Infrastructure

```bash
# Staging
cd environments/staging
terraform apply

# Production
cd environments/production
terraform apply
```

### Destroy Infrastructure

```bash
# Staging
cd environments/staging
terraform destroy

# Production
cd environments/production
terraform destroy
```

## Configuration

### Environment Variables

Set these in `terraform.tfvars`:

```hcl
gcp_project_id = "your-project-id"
gcp_region     = "us-central1"
environment    = "prod"
app_name       = "piehr"
alert_email    = "alerts@piehr.example.com"
dns_zone_name  = "piehr.example.com"
```

### Remote State Backend

Configure GCS backend in `backend.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket = "piehr-terraform-state-production"
    prefix = "terraform/state"
  }
}
```

## Cost Optimization

### Preemptible/Spot Nodes
- Spot node pool configured for cost savings
- Suitable for stateless workloads
- Can be tainted to prevent critical workloads

### Committed Use Discounts
- Consider purchasing committed use discounts for predictable workloads
- Can save up to 57% on compute costs

### Storage Lifecycle Policies
- Automatic transition to Coldline (90 days)
- Automatic transition to Archive (365 days)
- Reduces storage costs significantly

## Multi-Region Support

Multi-region deployment can be enabled by setting:

```hcl
enable_multi_region = true
secondary_region    = "us-east1"
```

This will create resources in both regions for disaster recovery.

## Security

### Network Security
- Private nodes (GKE)
- Private IP for Cloud SQL and Redis
- Network policies enabled
- VPC peering for private access

### Encryption
- KMS encryption for storage
- Transit encryption for Redis (production)
- SSL/TLS for database connections

### Access Control
- Workload Identity for GKE
- Least privilege IAM roles
- Service account isolation

## Monitoring and Alerts

### Alert Policies
- High error rate detection
- Resource utilization alerts
- Cost anomaly detection

### Notification Channels
- Email notifications
- Can be extended with PagerDuty, Slack, etc.

## Disaster Recovery

### Backups
- Automated daily backups (Cloud SQL)
- Point-in-time recovery (production)
- 30-day retention (production)

### Multi-Region
- Can be enabled for production
- Requires additional configuration

## Troubleshooting

### Common Issues

1. **API Not Enabled**: Enable required APIs
2. **Quota Exceeded**: Request quota increase
3. **Permission Denied**: Check IAM roles
4. **State Lock**: Check for stale locks in GCS

### Debug Commands

```bash
# Check Terraform state
terraform state list

# Show resource details
terraform state show <resource>

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive
```

## Next Steps

1. Configure remote state backend
2. Set up CI/CD for infrastructure changes
3. Enable cost monitoring
4. Set up backup verification
5. Configure disaster recovery procedures

## Outputs

After applying, Terraform outputs:
- Kubernetes cluster endpoint
- Cloud SQL connection details
- Redis host and port
- GCS bucket names
- Service account email
- DNS zone information

## Documentation

For more details, see:
- [GCP Documentation](https://cloud.google.com/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

