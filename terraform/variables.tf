variable "project_id" {
  type        = string
  description = "GCP project ID"
}
variable "region" {
  type        = string
  description = "Default GCP region"
  default     = "US"
}
variable "bucket_name" {
  type        = string
  description = "Globally unique GCS bucket name"
}
variable "service_account_email" {
  type        = string
  description = "Email of the existing pipeline service account"
}
variable "environment" {
  type        = string
  description = "Environment label"
  default     = "portfolio"
}
variable "dataset_ids" {
  type = set(string)
}

variable "required_apis" {
  type        = set(string)
  description = "Google Cloud APIs enabled for this project"
  default = [
    "bigquery.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
  ]
}

variable "labels" {
  type        = map(string)
  description = "Labels applied to supported resources"
  default = {
    managed_by = "terraform"
    workload   = "igdb-analytics"
  }
}

variable "bucket_lifecycle_delete_age_days" {
  type        = number
  description = "Delete bucket objects after this many days"
  default     = 365

  validation {
    condition     = var.bucket_lifecycle_delete_age_days > 0
    error_message = "bucket_lifecycle_delete_age_days must be greater than zero."
  }
}
