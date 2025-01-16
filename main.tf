terraform {
  required_version = ">= 1.6"

  required_providers {
	google = ">= 5.10"
  }
}

provider "google" {
  project = "${var.project_id}"
}


