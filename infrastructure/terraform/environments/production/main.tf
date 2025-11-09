module "infrastructure" {
  source = "../../"

  gcp_project_id = var.gcp_project_id
  gcp_region     = var.gcp_region
  environment    = "prod"
  app_name       = var.app_name

  # Database
  db_instance_tier = var.db_instance_tier
  db_disk_size     = var.db_disk_size
  database_name    = var.database_name
  database_user    = var.database_user

  # Redis
  redis_tier      = var.redis_tier
  redis_memory_gb = var.redis_memory_gb

  # GKE
  gke_initial_node_count = var.gke_initial_node_count
  gke_node_pool_size     = var.gke_node_pool_size
  gke_min_node_count     = var.gke_min_node_count
  gke_max_node_count     = var.gke_max_node_count
  gke_machine_type       = var.gke_machine_type

  # Networking
  subnet_cidr = var.subnet_cidr

  # DNS
  dns_zone_name = var.dns_zone_name
  alert_email   = var.alert_email

  # Security
  blocked_ip_ranges = var.blocked_ip_ranges

  # Multi-region
  enable_multi_region = var.enable_multi_region
  secondary_region    = var.secondary_region
}

