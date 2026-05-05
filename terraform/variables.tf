variable "source_code_repo_url" {
  type        = string
  description = "Repository where IaC and Lambda function source code resides"
}

variable "environment" {
  description = "Environment the infrastructure is deployed in"
  type        = string
}

variable "cost_centre" {
  description = "Cost centre to apply the resources too"
  type        = string
}

variable "api_gateway_name" {
  description = "Name of API Gateway"
  type        = string
}

variable "api_burst_limit" {
  description = "Maximum of requests allowed within a few milliseconds, allows temp spike in traffic over the rate limit"
  type        = number
}

variable "api_rate_limit" {
  description = "Maxmium number of requests per second the API can handle"
  type        = number
}

variable "api_gateway_usage_plan_name" {
  description = "Maxmium number of requests per second the API can handle"
  type        = string
}

variable "stage_name_api_gateway" {
  description = "Name of core AWS API gateway stage that is linked to deployment & usage plan"
  type        = string
}

variable "lambda_function_name" {
  type        = string
  description = "Name of lambda function"
}

variable "sns_topic_name" {
  type        = string
  description = "SNS topic name"
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
  description = "What does this stupid function do"
}

variable "enc_opensource_key" {
  type        = string
  description = "OpenSource API key for integration"
}

variable "enc_snyk_org1_key" {
  type        = string
  description = "Snyk API key for Org1 integration"
}

variable "enc_snyk_org2_key" {
  type        = string
  description = "Snyk API key for Org2 integration"
}

variable "cognito_oidc_userpool" {
  type        = string
  description = "Name of cognito userpool used to run OIDC service for client credential flow"
}

variable "cognito_domain_name" {
  type        = string
  description = "Cognito domain name (sub domain) to create when building out Oauth service"
}

variable "apigw_cognito_authorizer_name" {
  type        = string
  description = "Used to verify the token is legitimate when reaching API gateway"
}

variable "resource_server_identifier" {
  type        = string
  description = "Identifier for the Cognito resource server"
}

variable "resource_server_name" {
  type        = string
  description = "Name of the Cognito resource server"
}

variable "scope" {
  type        = string # Eventually this will be a list objects when we have more than 1 scope
  description = "Name of the scope to create within the resource server"
}

variable "cognito_oidc_client_app" {
  type        = string # Eventually this will be a list objects when we have more than 1 scope
  description = "Name of the Cognito OIDC client application"
}

variable "tenant_id" {
  type        = string
  description = "Microsoft Tenant ID used for authentication to the gateway"
}

variable "gateway_name" {
  type        = string
  description = "Name of the gateway"
}

variable "gateway_description" {
  type        = string
  description = "Description of the gateway"
}

variable "authorization_type" {
  type        = string
  description = "Authorization type used to authenticate to the gateway"
}

variable "audience_values" {
  type        = list(string)
  description = "List of audience values used for authentication to the gateway"
}
