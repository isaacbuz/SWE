gcp_project_id     = "your-project-dev"
gcp_region         = "us-central1"
environment        = "dev"
app_name           = "ai-company-platform"
subnet_cidr        = "10.0.0.0/24"

# Database configuration for dev
db_instance_tier   = "db-f1-micro"
db_disk_size       = 50
database_name      = "ai_company_db"
database_user      = "postgres"

# Redis configuration for dev
redis_tier         = "basic"
redis_memory_gb    = 1

# GKE configuration for dev
gke_initial_node_count = 1
gke_node_pool_size     = 1
gke_min_node_count     = 1
gke_max_node_count     = 3
gke_machine_type       = "e2-medium"
kube_namespace         = "default"
