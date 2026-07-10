output "bucket_name" {
  value       = module.gcs.bucket_name
  description = "Raw landing bucket"
}
output "dataset_ids" {
  value       = module.bigquery.dataset_ids
  description = "Analytics datasets"
}
output "service_account_email" {
  value       = var.service_account_email
  description = "Pipeline identity"
}
