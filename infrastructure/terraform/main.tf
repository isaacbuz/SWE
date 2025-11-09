terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }

  # Uncomment and configure for remote state management
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region

  default_labels {
    labels = {
      environment = var.environment
      managed_by  = "terraform"
      application = "ai-company-platform"
    }
  }
}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.gke_cluster.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.gke_cluster.master_auth[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.gke_cluster.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.gke_cluster.master_auth[0].cluster_ca_certificate)
  }
}

data "google_client_config" "default" {}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.app_name}-vpc-${var.environment}"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.app_name}-subnet-${var.environment}"
  ip_cidr_range = var.subnet_cidr
  region        = var.gcp_region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_logs_enabled    = true
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Cloud SQL Instance (PostgreSQL)
resource "google_sql_database_instance" "postgres" {
  name             = "${var.app_name}-postgres-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.gcp_region

  settings {
    tier              = var.db_instance_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.db_disk_size

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = var.environment == "prod" ? true : false
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled                                  = true
      private_network                               = google_compute_network.vpc.id
      enable_private_path_for_cloudsql_instance     = true
      require_ssl                                   = var.environment == "prod" ? true : false
      authorized_networks {
        value = "0.0.0.0/0"
        name  = "allow-all"
      }
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      query_plans_per_minute  = 5
    }
  }

  deletion_protection = var.environment == "prod" ? true : false

  depends_on = [google_service_networking_connection.private_vpc_connection]

  lifecycle {
    ignore_changes = [settings[0].backup_configuration[0].backup_retention_settings]
  }
}

resource "google_sql_database" "main" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "db_user" {
  name     = var.database_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Private VPC connection for Cloud SQL
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.app_name}-private-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

# Memorystore for Redis
resource "google_redis_instance" "cache" {
  name           = "${var.app_name}-redis-${var.environment}"
  region         = var.gcp_region
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_gb
  redis_version  = "7.0"

  auth_enabled            = true
  transit_encryption_mode = var.environment == "prod" ? "SERVER_AUTHENTICATION" : "DISABLED"

  display_name = "Redis Cache for ${var.app_name}"

  connect_mode = "PRIVATE_SERVICE_ACCESS"

  authorized_network = google_compute_network.vpc.id

  persistence_config {
    persistence_mode = var.environment == "prod" ? "RDB" : "DISABLED"
  }

  maintenance_policy {
    weekly_maintenance_window {
      day        = "SUNDAY"
      start_hour = 0
      end_hour   = 4
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Cloud Storage Bucket (GCS)
resource "google_storage_bucket" "app_bucket" {
  name          = "${var.app_name}-bucket-${var.environment}-${data.google_client_config.default.project}"
  location      = var.gcp_region
  force_destroy = var.environment != "prod" ? true : false

  uniform_bucket_level_access = true

  versioning {
    enabled = var.environment == "prod" ? true : false
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "ARCHIVE"
    }
  }

  logging {
    log_bucket = google_storage_bucket.log_bucket.name
  }
}

resource "google_storage_bucket" "log_bucket" {
  name          = "${var.app_name}-logs-${var.environment}-${data.google_client_config.default.project}"
  location      = var.gcp_region
  force_destroy = var.environment != "prod" ? true : false
}

# KMS Encryption Key
resource "google_kms_key_ring" "keyring" {
  name     = "${var.app_name}-keyring-${var.environment}"
  location = var.gcp_region
}

resource "google_kms_crypto_key" "storage_key" {
  name            = "${var.app_name}-storage-key-${var.environment}"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "7776000s" # 90 days
}

# GKE Cluster
resource "google_container_cluster" "gke_cluster" {
  name     = "${var.app_name}-gke-${var.environment}"
  location = var.gcp_region

  initial_node_count       = var.gke_initial_node_count
  remove_default_node_pool = true

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
  }

  network_policy {
    enabled = true
  }

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  resource_labels = {
    environment = var.environment
    application = var.app_name
  }
}

# GKE Node Pool - Default Pool
resource "google_container_node_pool" "primary" {
  name           = "${var.app_name}-node-pool-${var.environment}"
  cluster        = google_container_cluster.gke_cluster.id
  node_count     = var.gke_node_pool_size
  machine_type   = var.gke_machine_type

  autoscaling {
    min_node_count = var.gke_min_node_count
    max_node_count = var.gke_max_node_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.gke_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    taint {
      key    = "environment"
      value  = var.environment
      effect = "NO_SCHEDULE"
    }

    labels = {
      environment = var.environment
      application = var.app_name
      pool-type   = "default"
    }

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

# GKE Node Pool - Spot/Preemptible Pool (Cost Optimization)
resource "google_container_node_pool" "spot" {
  name     = "${var.app_name}-spot-pool-${var.environment}"
  cluster  = google_container_cluster.gke_cluster.id
  location = var.gcp_region

  autoscaling {
    min_node_count = 0
    max_node_count = 5
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type  = var.gke_machine_type
    disk_size_gb  = 100
    disk_type     = "pd-standard"
    preemptible   = true
    spot          = true

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      application = var.app_name
      pool-type   = "spot"
    }

    taints {
      key    = "spot"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }
}

# Service Account
resource "google_service_account" "gke_sa" {
  account_id   = "${var.app_name}-gke-${var.environment}"
  display_name = "Service Account for ${var.app_name} GKE"
}

resource "google_project_iam_member" "gke_sa_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/storage.objectViewer"
  ])

  project = data.google_client_config.default.project
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_sa.email}"
}

# Workload Identity binding
resource "google_service_account_iam_member" "workload_identity" {
  service_account_id = google_service_account.gke_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${data.google_client_config.default.project}.svc.id.goog[${var.kube_namespace}/${var.app_name}-ksa]"
}

# Cloud DNS Zone
resource "google_dns_managed_zone" "piehr_zone" {
  name        = "${var.app_name}-zone-${var.environment}"
  dns_name    = var.dns_zone_name
  description = "DNS zone for ${var.app_name} ${var.environment}"

  visibility = "public"

  dnssec_config {
    state = "on"
  }
}

# Cloud DNS Records
resource "google_dns_record_set" "api" {
  name         = "api.${google_dns_managed_zone.piehr_zone.dns_name}"
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.piehr_zone.name
  rrdatas      = [google_compute_global_address.lb_ip.address]
}

resource "google_dns_record_set" "web" {
  name         = google_dns_managed_zone.piehr_zone.dns_name
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.piehr_zone.name
  rrdatas      = [google_compute_global_address.lb_ip.address]
}

# Global IP Address for Load Balancer
resource "google_compute_global_address" "lb_ip" {
  name         = "${var.app_name}-lb-ip-${var.environment}"
  address_type = "EXTERNAL"
  ip_version   = "IPV4"
}

# Cloud Armor Security Policy
resource "google_compute_security_policy" "armor_policy" {
  name        = "${var.app_name}-armor-${var.environment}"
  description = "Cloud Armor security policy for ${var.app_name}"

  # Default rule - allow all
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }

  # Rate limiting rule
  rule {
    action   = "throttle"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
    }
    description = "Rate limiting rule"
  }

  # Block known bad IPs
  rule {
    action   = "deny(403)"
    priority = "100"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = var.blocked_ip_ranges
      }
    }
    description = "Block known bad IP ranges"
  }
}

# Cloud Monitoring Notification Channel (Email)
resource "google_monitoring_notification_channel" "email" {
  display_name = "${var.app_name}-email-${var.environment}"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
}

# Cloud Monitoring Alert Policy - High Error Rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "${var.app_name} High Error Rate"
  combiner     = "OR"
  conditions {
    display_name = "Error rate too high"
    condition_threshold {
      filter          = "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${google_container_cluster.gke_cluster.name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  notification_channels = [google_monitoring_notification_channel.email.name]
  enabled               = true
}
