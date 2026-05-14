variable "tags" {
  type        = map(string)
  description = "Tags to apply to the gateway"
}

variable "opensource_dynamodb_table_name" {
  type        = string
  description = "Name of DynamoDB table for IOCs"
}

variable "opensource_dynamodb_hash_key" {
  type        = string
  description = "DynamoDB sort key for IOCs"
}

variable "opensource_dynamodb_range_key" {
  type        = string
  description = "DynamoDB partition key for IOCs"
}
