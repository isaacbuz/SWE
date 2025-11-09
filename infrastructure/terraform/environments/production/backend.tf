terraform {
  backend "gcs" {
    bucket = "piehr-terraform-state-production"
    prefix = "terraform/state"
  }
}

