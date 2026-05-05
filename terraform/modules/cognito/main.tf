resource "aws_cognito_user_pool" "oidc_userpool" {
  name           = var.cognito_oidc_userpool
  user_pool_tier = "LITE"
  tags           = var.tags
}

resource "aws_cognito_user_pool_domain" "cognito_domain" {
  domain       = var.cognito_domain_name
  user_pool_id = aws_cognito_user_pool.oidc_userpool.id
}

resource "aws_cognito_resource_server" "sca_api_resource_server" {
  identifier = var.resource_server_identifier
  name       = var.resource_server_name

  scope {
    scope_name        = var.scope
    scope_description = "Scope that has access to check SCA data"
  }

  user_pool_id = aws_cognito_user_pool.oidc_userpool.id
}

resource "aws_cognito_user_pool_client" "bedrock_gateway" {
  name                                 = var.cognito_oidc_client_app
  generate_secret                      = true
  access_token_validity                = 1
  refresh_token_validity               = 1
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials"]
  allowed_oauth_scopes                 = ["${var.resource_server_identifier}/${var.scope}"]
  enable_token_revocation              = true
  explicit_auth_flows                  = ["ALLOW_REFRESH_TOKEN_AUTH"]
  user_pool_id                         = aws_cognito_user_pool.oidc_userpool.id
}
