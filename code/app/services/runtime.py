from app.services.aws import AWSClient
from app.services.dynamodb import DynamoDBService

aws_client = AWSClient(region="ap-southeast-2")
dynamodb_client = DynamoDBService(region="ap-southeast-2")
