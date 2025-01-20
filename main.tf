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

resource "google_project_service" "cloud_sql_admin" {
  service = "sqladmin.googleapis.com"
  project = "gcp-projekt-442288"
}

resource "google_sql_database_instance" "instance" {
  name              = "weather-data"
  database_version  = "POSTGRES_15"
  region            = "us-central1"
  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled = true
    }
  }
  deletion_protection = false

  depends_on = [google_project_service.cloud_sql_admin]
}


resource "google_sql_database" "database" {
  name     = "weather-data"
  instance = google_sql_database_instance.instance.name

  depends_on = [google_sql_database_instance.instance]
}

resource "google_sql_user" "users" {
  name     = "postgres"
  instance = google_sql_database_instance.instance.name
  password = "postgres"

  depends_on = [google_sql_database_instance.instance]
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

    environment_variables = {
      DB_USER             = "postgres"
      DB_PASSWORD         = "postgres"
      DB_NAME             = "weather-data"
      DB_CONNECTION_NAME  = google_sql_database_instance.instance.connection_name
    }
  }
}


resource "google_project_service" "cloud_resource_manager" {
  service = "cloudresourcemanager.googleapis.com"
  project = "gcp-projekt-442288"
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

output "function_uri" {
  value = google_cloudfunctions2_function.fetch-data-api.service_config[0].uri
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


