# terraform/outputs.tf

output "ec2_public_ip" {
  value = aws_instance.app_server.public_ip
}

output "rds_host" { 
  value = aws_db_instance.postgres.address 
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

