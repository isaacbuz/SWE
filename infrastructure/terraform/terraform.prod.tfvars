gcp_project_id     = "your-project-prod"
gcp_region         = "us-central1"
environment        = "prod"
app_name           = "ai-company-platform"
subnet_cidr        = "10.0.0.0/24"

# Database configuration for prod
db_instance_tier   = "db-custom-2-7680"
db_disk_size       = 500
database_name      = "ai_company_db"
database_user      = "postgres"

# Redis configuration for prod
redis_tier         = "standard"
redis_memory_gb    = 10

# GKE configuration for prod
gke_initial_node_count = 3
gke_node_pool_size     = 3
gke_min_node_count     = 3
gke_max_node_count     = 10
gke_machine_type       = "e2-standard-4"
kube_namespace         = "production"
