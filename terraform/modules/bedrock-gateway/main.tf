data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_bedrockagentcore_gateway" "gateway" {
  name            = var.gateway_name
  description     = var.gateway_description
  role_arn        = aws_iam_role.gateway_role.arn
  authorizer_type = var.authorization_type
  protocol_type   = "MCP"
  region          = data.aws_region.current.name
  authorizer_configuration {
    custom_jwt_authorizer {
      discovery_url    = "https://login.microsoftonline.com/${var.tenant_id}/v2.0/.well-known/openid-configuration"
      allowed_audience = var.audience_values
    }
  }
  tags = var.tags
}

resource "aws_bedrockagentcore_oauth2_credential_provider" "cognito_idp_provider" {
  name = var.cognito_idp_provider_name

  credential_provider_vendor = "CustomOauth2"
  oauth2_provider_config {
    custom_oauth2_provider_config {
      client_id_wo                  = var.cognito_client_id
      client_secret_wo              = var.cognito_client_secret
      client_credentials_wo_version = 1

      oauth_discovery {
        authorization_server_metadata {
          issuer                 = "https://${var.cognito_domain_name}.auth.${data.aws_region.current.name}.amazoncognito.com"
          authorization_endpoint = "https://${var.cognito_domain_name}.auth.${data.aws_region.current.name}.amazoncognito.com/oauth2/identity"
          token_endpoint         = "https://${var.cognito_domain_name}.auth.${data.aws_region.current.name}.amazoncognito.com/oauth2/token"
          response_types         = ["code"]
        }
      }
    }
  }
}

resource "aws_bedrockagentcore_gateway_target" "sca_api" {
  name               = "SCAAPIModern"
  gateway_identifier = aws_bedrockagentcore_gateway.gateway.gateway_id
  description        = "This gateway enables our existing SCA API to be accessible via MCP"
  region             = data.aws_region.current.name

  credential_provider_configuration {
    oauth {
      provider_arn = aws_bedrockagentcore_oauth2_credential_provider.cognito_idp_provider.credential_provider_arn
      grant_type   = "CLIENT_CREDENTIALS"
      scopes       = var.oauth_scopes
    }
  }

  target_configuration {
    mcp {
      open_api_schema {
        inline_payload {
          payload = file("${path.module}/../../../openapi.yaml")
        }
      }
    }
  }
}

#################### IAM #############################
data "aws_iam_policy_document" "assume_role_gateway" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "gateway_role" {
  name               = "bedrock-agentcore-gateway-role-${var.gateway_name}"
  assume_role_policy = data.aws_iam_policy_document.assume_role_gateway.json
}

resource "aws_iam_role_policy_attachment" "default_policy_attachment_lambda_role_gateway" {
  role       = aws_iam_role.gateway_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "bedrock_agent_custom_execution_policy" {
  version = "2012-10-17"
  statement {
    sid    = "AllowBedrockAgentCoreAccessToken"
    effect = "Allow"
    actions = [
      "bedrock-agentcore:GetWorkloadAccessToken",
      "bedrock-agentcore:GetResourceOauth2Token",
    ]
    resources = [
      "arn:aws:bedrock-agentcore:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:workload-identity-directory/default",
      "arn:aws:bedrock-agentcore:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:workload-identity-directory/default/workload-identity/${var.gateway_name}-*"
    ]
  }
  statement {
    sid    = "AllowBedrockAgentCoreAuth2"
    effect = "Allow"
    actions = [
      "bedrock-agentcore:GetResourceOauth2Token",
    ]
    resources = [
      "arn:aws:bedrock-agentcore:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:token-vault/default*",
    ]
  }
  statement {
    sid    = "GetSecretValue"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
         "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:*"
    ]
  }
}

resource "aws_iam_policy" "bedrock_agent_custom_execution_policy" {
  name   = "agentcore-${var.gateway_name}-agentcore-policy"
  policy = data.aws_iam_policy_document.bedrock_agent_custom_execution_policy.json
  tags   = var.tags
}

resource "aws_iam_policy_attachment" "policy_attachment_agentcore" {
  name       = "role-policy-attachment-${var.gateway_name}"
  roles      = [aws_iam_role.gateway_role.name]
  policy_arn = aws_iam_policy.bedrock_agent_custom_execution_policy.arn
}
