provider "aws" {
  region = "eu-north-1"
}

resource "aws_s3_bucket" "data_lake" {
  bucket = "sbb-data-lake-jon-stojkaj"
}

resource "aws_db_instance" "sbb_postgres" {
  identifier           = "sbb-postgres-db"
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "16.3"
  instance_class       = "db.t4g.micro"
  username             = "postgres"
  password             = var.db_password
  storage_encrypted    = true
  publicly_accessible  = false
  skip_final_snapshot  = true
}

resource "aws_iam_role" "lambda_exec" {
  name = "sbb_lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_ssm" {
  name = "sbb-lambda-read-parameters"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameter"]
      Resource = "arn:aws:ssm:eu-north-1:*:parameter/sbb/db_password"
    }]
  })
}

resource "aws_lambda_function" "sbb_etl" {
  function_name = "sbb-pipeline-etl"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.12"
  filename      = "lambda_package.zip"
  timeout       = 30

  environment {
    variables = {
      DB_HOST        = aws_db_instance.sbb_postgres.address
      DB_USER        = "postgres"
      DB_NAME        = "postgres"
      S3_BUCKET_NAME = aws_s3_bucket.data_lake.bucket
    }
  }
}