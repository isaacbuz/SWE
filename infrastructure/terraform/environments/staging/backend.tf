terraform {
  backend "gcs" {
    bucket = "piehr-terraform-state-staging"
    prefix = "terraform/state"
  }
}

