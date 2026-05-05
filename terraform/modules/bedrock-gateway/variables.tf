variable "tags" {
  type        = map(string)
  description = "Tags to apply to the gateway"
}

variable "tenant_id" {
  type        = string
  description = "Microsoft Tenant ID used for authentication to the gateway"
}

variable "audience_values" {
  type        = list(string)
  description = "List of audience values used for authentication to the gateway"
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

variable "oauth_scopes" {
  type        = list(string)
  description = "Scopes needed for the oauth provider to access API gateway"
}

variable "cognito_client_id" {
  type        = string
  description = "Client ID for the oauth provider to access API gateway"
}

variable "cognito_client_secret" {
  type        = string
  description = "Client secret for the oauth provider to access API gateway"
  sensitive   = true
}

variable "cognito_idp_provider_name" {
  type        = string
  description = "Name of the Cognito IDP provider for service API gateway for MCP"
}

variable "cognito_domain_name" {
  type        = string
  description = "Cognito domain name for the user pool"
}
