terraform {
  required_version = ">= 1.5"

  required_providers {
    google = ">= 5.10"
  }
}

provider "google" {
  project = "gcp-projekt-442288"
  region  = "us-central1"
}

resource "google_project_service" "cloud_run_api" {
  service = "run.googleapis.com"
  project = "gcp-projekt-442288"
  disable_on_destroy = false
}

resource "google_storage_bucket" "cloud-functions-bucket" {
  name     = "cloud-functions-bucket-gcp-projekt-442288"
  location = "us-central1"
}

resource "google_storage_bucket_object" "cloud-functions-zip" {
  name   = "cloud-functions-zip"
  bucket = google_storage_bucket.cloud-functions-bucket.name
  source = "cloud-functions.zip"
}

resource "google_cloudfunctions2_function" "fetch-data-api" {
  name        = "fetch-data-api"
  location    = "us-central1"
  description = "Function fetch data and save them to database"

  build_config {
    runtime     = "python310"
    entry_point = "return_data"
    source {
      storage_source {
        bucket = google_storage_bucket.cloud-functions-bucket.name
        object = google_storage_bucket_object.cloud-functions-zip.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "256M"
  }
}

resource "google_project_service" "cloud_resource_manager" {
  service = "cloudresourcemanager.googleapis.com"
  project = "gcp-projekt-442288"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_scheduler" {
  service = "cloudscheduler.googleapis.com"
  project = "gcp-projekt-442288"

  depends_on = [google_project_service.cloud_resource_manager]
}

resource "google_cloud_run_service_iam_member" "member" {
  location = google_cloudfunctions2_function.fetch-data-api.location
  service  = google_cloudfunctions2_function.fetch-data-api.service_config[0].service
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_scheduler_job" "schedule-fetch-data-api" {
  name         = "schedule-fetch-data-api"
  description  = "Scheduler for fetch data and save them to database"
  schedule     = "1,16,31,46 * * * *"
  region       = "us-central1"

  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions2_function.fetch-data-api.service_config[0].uri
  }

  depends_on = [google_cloudfunctions2_function.fetch-data-api]
}

resource "google_cloud_run_service_iam_member" "all_users" {
  location = "us-central1" 
  project  = "gcp-projekt-442288"  
  service  = google_cloud_run_service.weather_app.name

  role    = "roles/run.invoker"
  member  = "allUsers" 
}

resource "google_project_service" "container_registry_api" {
  service = "containerregistry.googleapis.com"
}

resource "google_cloud_run_service" "weather_app" {
  name     = "weather-app-flask"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/app"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.cloud_run_api,
    google_project_service.container_registry_api
  ]
}

output "function_uri" {
  value = google_cloudfunctions2_function.fetch-data-api.service_config[0].uri
}

output "weather_app_url" {
  value = google_cloud_run_service.weather_app.status[0].url
}

