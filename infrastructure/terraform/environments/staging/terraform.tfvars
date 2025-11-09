gcp_project_id = "your-project-id"
gcp_region     = "us-central1"
environment    = "staging"
app_name       = "piehr"

# Database
db_instance_tier = "db-f1-micro"
db_disk_size     = 50
database_name    = "piehr"
database_user    = "piehr_user"

# Redis
redis_tier      = "basic"
redis_memory_gb = 1

# GKE
gke_initial_node_count = 1
gke_node_pool_size     = 1
gke_min_node_count     = 1
gke_max_node_count     = 3
gke_machine_type       = "e2-standard-2"

# Networking
subnet_cidr = "10.0.0.0/24"

# DNS
dns_zone_name = "staging.piehr.example.com"
alert_email   = "alerts@piehr.example.com"

# Security
blocked_ip_ranges = []

# Multi-region
enable_multi_region = false

