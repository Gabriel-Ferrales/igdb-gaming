output "dataset_ids" { value = sort([for dataset in google_bigquery_dataset.this : dataset.dataset_id]) }
