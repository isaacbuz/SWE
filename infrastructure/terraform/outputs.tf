output "kubernetes_cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.gke_cluster.name
}

output "kubernetes_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.gke_cluster.endpoint
  sensitive   = true
}

output "kubernetes_cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.gke_cluster.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cloud_sql_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "cloud_sql_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.cache.host
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.cache.port
}

output "gcs_bucket_name" {
  description = "GCS bucket name for application artifacts"
  value       = google_storage_bucket.app_bucket.name
}

output "gcs_log_bucket_name" {
  description = "GCS bucket name for logs"
  value       = google_storage_bucket.log_bucket.name
}

output "vpc_network_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "vpc_subnet_name" {
  description = "VPC subnet name"
  value       = google_compute_subnetwork.subnet.name
}

output "service_account_email" {
  description = "GKE service account email"
  value       = google_service_account.gke_sa.email
}

output "kms_key_name" {
  description = "KMS encryption key name"
  value       = google_kms_crypto_key.storage_key.id
}

