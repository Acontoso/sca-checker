variable "tags" {
  type        = map(string)
  description = "Tags to apply to the gateway"
}

variable "cognito_oidc_userpool" {
  type        = string
  description = "Name of the Cognito OIDC user pool"
}

variable "cognito_domain_name" {
  type        = string
  description = "Cognito domain name for the user pool"
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
