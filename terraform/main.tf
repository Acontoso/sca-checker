locals {
  tags = merge(
    {
      "env"        = "${var.environment}"
      "terraform"  = "true"
      "bu"         = "security"
      "RepoUrl"    = "${var.source_code_repo_url}"
      "service"    = "sca-api"
      "author"     = "alex skoro"
      "costcentre" = "${var.cost_centre}"
    }
  )
  aws_region = "ap-southeast-2"
}

data "aws_kms_key" "ssm_kms_alias" {
  key_id = "alias/cmk-ssm"
}

module "sns" {
  source         = "./modules/sns"
  sns_topic_name = var.sns_topic_name
  tags           = local.tags
}

module "ssm_parameters" {
  source     = "./modules/ssm"
  kms_key_id = data.aws_kms_key.ssm_kms_alias.id
  tags       = local.tags

  parameters = {
    synorg1 = {
      name        = "/snyk_token/orgid1"
      description = "Snyk token for Org1"
      value       = var.enc_snyk_org1_key
    }
    synorg2 = {
      name        = "/snyk_token/orgid2"
      description = "Snyk token key for Org2"
      value       = var.enc_snyk_org2_key
    }
    OpenSource = {
      name        = "/snyk_token/opensourceapi"
      description = "API key for opensource API"
      value       = var.enc_opensource_key
    }
  }
}

module "cognito" {
  source                     = "./modules/cognito"
  tags                       = local.tags
  cognito_oidc_userpool      = var.cognito_oidc_userpool
  cognito_domain_name        = var.cognito_domain_name
  resource_server_identifier = var.resource_server_identifier
  resource_server_name       = var.resource_server_name
  scope                      = var.scope
  cognito_oidc_client_app    = var.cognito_oidc_client_app
}

module "lambda" {
  source                 = "./modules/lambda"
  tags                   = local.tags
  lambda_function_name   = var.lambda_function_name
  runtime                = var.runtime
  handler                = var.handler
  memory_size            = var.memory_size
  timeout                = var.timeout
  description            = var.description
  sns_topic_arn          = module.sns.sns_arn
  cognito_region         = local.aws_region
  cognito_user_pool_id   = module.cognito.aws_cognito_user_pool_id
  cognito_required_scope = "sca-api/ioc.lookup.all"
}

module "apigateway" {
  source                         = "./modules/apigateway"
  tags                           = local.tags
  api_gateway_name               = var.api_gateway_name
  api_rate_limit                 = var.api_rate_limit
  api_burst_limit                = var.api_burst_limit
  api_gateway_usage_plan_name    = var.api_gateway_usage_plan_name
  aws_lambda_function_name       = module.lambda.lambda_function_name
  aws_lambda_function_invoke_arn = module.lambda.lambda_function_invoke_arn
  stage_name_api_gateway         = var.stage_name_api_gateway
  apigw_cognito_authorizer_name  = var.apigw_cognito_authorizer_name
  cognito_user_pool_arn          = module.cognito.aws_cognito_user_pool_arn
  aws_lambda_function_arn        = module.lambda.lambda_function_arn
}

module "bedrockgateway" {
  source                    = "./modules/bedrock-gateway"
  tags                      = local.tags
  tenant_id                 = var.tenant_id
  gateway_name              = var.gateway_name
  gateway_description       = var.gateway_description
  authorization_type        = var.authorization_type
  audience_values           = var.audience_values
  oauth_scopes              = ["sca-api/ioc.lookup.all"]
  cognito_client_id         = module.cognito.aws_cognito_user_pool_client_id
  cognito_client_secret     = module.cognito.aws_cognito_user_pool_client_secret
  cognito_domain_name       = var.cognito_domain_name
  cognito_idp_provider_name = "entraIDSCA"
}
