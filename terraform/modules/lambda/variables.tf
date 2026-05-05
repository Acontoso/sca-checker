variable "lambda_function_name" {
  type        = string
  description = "Name of lambda function"
}

variable "runtime" {
  type        = string
  description = "Lambda runtime language and version"
}

variable "handler" {
  type        = string
  description = "Specify file & main entry point of Lambda function"
}

variable "memory_size" {
  type        = string
  description = "Size of memory to allocate Lambda function during runtime"
}

variable "timeout" {
  type        = number
  description = "Lambda function timeout"
}

variable "description" {
  type        = string
  description = "Description of the Lambda function"
}

variable "sns_topic_arn" {
  type        = string
  description = "ARN of the SNS topic to allow failures to be published from the Lambda function"
}

variable "cognito_region" {
  type        = string
  description = "AWS region for the Cognito user pool issuer"
}

variable "cognito_user_pool_id" {
  type        = string
  description = "Cognito user pool ID used to validate inbound JWTs"
}

variable "cognito_required_scope" {
  type        = string
  description = "Required Cognito scope for protected API routes"
  default     = "sca-api/ioc.lookup.all"
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to the Lambda function"
}

variable "ssm_param_path_api_key" {
  type        = string
  description = "Path of the SSM parameter that contains the API key"
  default     = "/snyk_token/*"
}
