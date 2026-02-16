# terraform/variables.tf

variable "aws_region" {
  description = "The AWS region to deploy into"
  default     = "eu-north-1"
}

variable "project_name" {
  description = "The name of the project (used for tags)"
  default     = "transaction-api"
}

variable "db_password" {
  description = "The password for the RDS database"
  type        = string
  sensitive   = true
}

variable "public_key" {
  description = "SSH Public key for EC2 access"
  type        = string
}

