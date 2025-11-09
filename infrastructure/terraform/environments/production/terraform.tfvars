gcp_project_id = "your-project-id"
gcp_region     = "us-central1"
environment    = "prod"
app_name       = "piehr"

# Database
db_instance_tier = "db-n1-standard-4"
db_disk_size     = 100
database_name    = "piehr"
database_user    = "piehr_user"

# Redis
redis_tier      = "standard"
redis_memory_gb = 4

# GKE
gke_initial_node_count = 3
gke_node_pool_size     = 3
gke_min_node_count     = 3
gke_max_node_count     = 10
gke_machine_type       = "e2-standard-4"

# Networking
subnet_cidr = "10.0.0.0/24"

# DNS
dns_zone_name = "piehr.example.com"
alert_email   = "alerts@piehr.example.com"

# Security
blocked_ip_ranges = []

# Multi-region
enable_multi_region = true
secondary_region    = "us-east1"

