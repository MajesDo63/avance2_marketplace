terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# 1. Bucket S3 para evidencias y comprobantes del Marketplace
resource "aws_s3_bucket" "marketplace_bucket" {
  bucket = "marketplace-datos-protegidos-cesar-lsca2314"
}

# Cifrado obligatorio en reposo con SSE-S3 (AES256)
resource "aws_s3_bucket_server_side_encryption_configuration" "s3_cifrado" {
  bucket = aws_s3_bucket.marketplace_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bloqueo total de acceso publico
resource "aws_s3_bucket_public_access_block" "bloqueo_publico" {
  bucket = aws_s3_bucket.marketplace_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 2. Base de datos RDS (PostgreSQL) privada y cifrada
resource "aws_db_instance" "marketplace_rds" {
  identifier             = "marketplace-db"
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = "db.t3.micro"
  username               = "dbadmin"
  password               = "ClaveTemporalSegura2026!" # Variable inyectada en despliegue
  publicly_accessible    = false
  storage_encrypted      = true
  skip_final_snapshot    = true
}
