variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "ai-company-platform"
}

variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.0.0.0/24"
}

# Database Variables
variable "db_instance_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"

  validation {
    condition     = contains(["db-f1-micro", "db-g1-small", "db-custom-1-3840", "db-custom-2-7680"], var.db_instance_tier)
    error_message = "Select a valid Cloud SQL tier."
  }
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 50
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "ai_company_db"
}

variable "database_user" {
  description = "Database user"
  type        = string
  default     = "postgres"
}

# Redis Variables
variable "redis_tier" {
  description = "Redis tier (basic or standard)"
  type        = string
  default     = "basic"

  validation {
    condition     = contains(["basic", "standard"], var.redis_tier)
    error_message = "Redis tier must be basic or standard."
  }
}

variable "redis_memory_gb" {
  description = "Redis memory in GB"
  type        = number
  default     = 1

  validation {
    condition     = var.redis_memory_gb >= 1 && var.redis_memory_gb <= 300
    error_message = "Redis memory must be between 1 and 300 GB."
  }
}

# GKE Variables
variable "gke_initial_node_count" {
  description = "Initial number of nodes in GKE cluster"
  type        = number
  default     = 3
}

variable "gke_node_pool_size" {
  description = "Number of nodes in the node pool"
  type        = number
  default     = 3
}

variable "gke_min_node_count" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "gke_max_node_count" {
  description = "Maximum number of nodes"
  type        = number
  default     = 5
}

variable "gke_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "kube_namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "dns_zone_name" {
  description = "DNS zone name (e.g., piehr.example.com)"
  type        = string
  default     = "piehr.example.com"
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
