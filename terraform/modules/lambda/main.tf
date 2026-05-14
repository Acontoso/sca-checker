resource "aws_lambda_function" "lambda" {
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_role.arn
  description      = var.description
  filename         = data.archive_file.code.output_path
  source_code_hash = data.archive_file.code.output_base64sha256
  handler          = var.handler
  runtime          = var.runtime
  memory_size      = var.memory_size
  tags             = var.tags
  timeout          = var.timeout
  logging_config {
    log_format = "JSON"
  }
  environment {
    variables = {
      COGNITO_REGION                 = var.cognito_region
      COGNITO_USER_POOL_ID           = var.cognito_user_pool_id
      COGNITO_REQUIRED_SCOPE         = var.cognito_required_scope
      OPENSOURCE_DYNAMODB_TABLE_NAME = var.opensource_dynamodb_table_name
      OPENSOURCE_DYNAMODB_HASH_KEY   = var.opensource_dynamodb_hash_key
      OPENSOURCE_DYNAMODB_RANGE_KEY  = var.opensource_dynamodb_range_key
    }
  }
}

resource "null_resource" "pip_install" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "python3 -m pip install --upgrade --force-reinstall --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: -r ${path.module}/../../../requirements.txt -t ${path.module}/../../../code"
  }
}

data "archive_file" "code" {
  type        = "zip"
  source_dir  = "${path.module}/../../../code"
  output_path = "${path.module}/../../../code.zip"
  depends_on  = [null_resource.pip_install]
}

resource "aws_lambda_function_event_invoke_config" "lambda_retry_failure" {
  function_name                = aws_lambda_function.lambda.function_name
  maximum_event_age_in_seconds = 21600
  maximum_retry_attempts       = 0
  destination_config {
    on_failure {
      destination = var.sns_topic_arn
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_kms_key" "ssm_kms_alias" {
  key_id = "alias/cmk-ssm"
}

#################################Lambda####################################
data "aws_iam_policy_document" "trust_policy_document_lambda" {
  statement {
    sid    = "LambdaTrustPolicy"
    effect = "Allow"

    actions = [
      "sts:AssumeRole",
    ]

    principals {
      identifiers = [
        "lambda.amazonaws.com",
      ]

      type = "Service"
    }
  }
}

data "aws_iam_policy_document" "lambda_custom_execution_policy" {
  version = "2012-10-17"
  statement {
    sid    = "AllowSSM"
    effect = "Allow"
    actions = [
      "ssm:GetParameter*"
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.ssm_param_path_api_key}"
    ]
  }
  statement {
    sid    = "AllowSnsPublish"
    effect = "Allow"
    actions = [
      "sns:Publish",
    ]
    resources = [
      var.sns_topic_arn
    ]
  }
  statement {
    sid    = "AllowKMS"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
    ]
    resources = [
      data.aws_kms_key.ssm_kms_alias.arn
    ]
  }
}

resource "aws_iam_policy" "lambda_iam_policy" {
  name   = "sca-api-lambda-policy"
  policy = data.aws_iam_policy_document.lambda_custom_execution_policy.json
  tags   = var.tags
}

resource "aws_iam_policy_attachment" "lambda_policy_attachment_role" {
  name       = "sca-api-lambda-policy-attachment"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = aws_iam_policy.lambda_iam_policy.arn
}

resource "aws_iam_role" "lambda_role" {
  name               = "sca-api-lambda-execution-role"
  assume_role_policy = data.aws_iam_policy_document.trust_policy_document_lambda.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "default_policy_attachment_lambda_role" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
