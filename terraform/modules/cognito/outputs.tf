output "aws_cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.oidc_userpool.id
}

output "aws_cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.oidc_userpool.arn
}

output "aws_cognito_user_pool_client_id" {
  description = "Client ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.bedrock_gateway.id
}

output "aws_cognito_user_pool_client_secret" {
  description = "Client secret of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.bedrock_gateway.client_secret
  sensitive   = true
}
