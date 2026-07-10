resource "google_bigquery_dataset" "this" {
  for_each                   = var.dataset_ids
  project                    = var.project_id
  dataset_id                 = each.value
  location                   = var.location
  delete_contents_on_destroy = false
}
