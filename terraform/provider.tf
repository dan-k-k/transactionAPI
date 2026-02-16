# terraform/provider.tf

provider "aws" {
  region = var.aws_region
}

terraform {
  backend "s3" {
    bucket         = "dans-transaction-api-tf-state-1"
    key            = "transaction-api/terraform.tfstate"
    region         = "eu-north-1"
    encrypt        = true
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

