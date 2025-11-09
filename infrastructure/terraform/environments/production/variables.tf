variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
}

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "db_instance_tier" {
  description = "Cloud SQL instance tier"
  type        = string
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
}

variable "database_name" {
  description = "Database name"
  type        = string
}

variable "database_user" {
  description = "Database user"
  type        = string
}

variable "redis_tier" {
  description = "Redis tier"
  type        = string
}

variable "redis_memory_gb" {
  description = "Redis memory in GB"
  type        = number
}

variable "gke_initial_node_count" {
  description = "Initial number of nodes"
  type        = number
}

variable "gke_node_pool_size" {
  description = "Number of nodes in node pool"
  type        = number
}

variable "gke_min_node_count" {
  description = "Minimum number of nodes"
  type        = number
}

variable "gke_max_node_count" {
  description = "Maximum number of nodes"
  type        = number
}

variable "gke_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
}

variable "subnet_cidr" {
  description = "CIDR range for subnet"
  type        = string
}

variable "dns_zone_name" {
  description = "DNS zone name"
  type        = string
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
}

variable "blocked_ip_ranges" {
  description = "List of IP ranges to block"
  type        = list(string)
  default     = []
}

variable "enable_multi_region" {
  description = "Enable multi-region deployment"
  type        = bool
  default     = false
}

variable "secondary_region" {
  description = "Secondary region for multi-region deployment"
  type        = string
  default     = "us-east1"
}

