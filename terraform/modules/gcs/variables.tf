variable "project_id" { type = string }
variable "bucket_name" { type = string }
variable "location" { type = string }
variable "labels" { type = map(string) }
variable "lifecycle_delete_age_days" { type = number }
