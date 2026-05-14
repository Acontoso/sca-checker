module "dynamodb_table_opensource" {
  source  = "terraform-aws-modules/dynamodb-table/aws"
  version = "5.5.0"

  name                        = var.opensource_dynamodb_table_name
  hash_key                    = var.opensource_dynamodb_hash_key
  range_key                   = var.opensource_dynamodb_range_key
  deletion_protection_enabled = true
  ttl_enabled                 = true
  ttl_attribute_name          = "expires_at"

  attributes = [
    {
      name = var.opensource_dynamodb_hash_key
      type = "S"
    },
    {
      name = var.opensource_dynamodb_range_key
      type = "S"
    }
  ]

  tags = var.tags
}
