resource "google_project_service" "required" {
  for_each = var.required_apis

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

module "gcs" {
  source                    = "./modules/gcs"
  bucket_name               = var.bucket_name
  location                  = var.region
  project_id                = var.project_id
  labels                    = merge(var.labels, { environment = var.environment })
  lifecycle_delete_age_days = var.bucket_lifecycle_delete_age_days

  depends_on = [google_project_service.required]
}

module "bigquery" {
  source      = "./modules/bigquery"
  project_id  = var.project_id
  location    = var.region
  dataset_ids = var.dataset_ids

  depends_on = [google_project_service.required]
}

module "iam" {
  source                = "./modules/iam"
  project_id            = var.project_id
  service_account_email = var.service_account_email
  bucket_name           = module.gcs.bucket_name

  depends_on = [google_project_service.required]
}
