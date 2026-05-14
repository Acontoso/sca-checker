import asyncio
from functools import partial
from typing import Any

import boto3
from boto3.dynamodb.conditions import ConditionBase
from botocore.exceptions import ClientError

from app.loggers.runtime_json_logger import logger

DEFAULT_REGION = "ap-southeast-2"


class DynamoDBService:
    """Async-compatible DynamoDB service.

    boto3 is synchronous, so each method offloads the blocking call to a
    thread-pool executor via ``run_in_executor``, keeping the FastAPI event
    loop unblocked.
    """

    def __init__(self, region: str = DEFAULT_REGION) -> None:
        self._resource = boto3.resource("dynamodb", region_name=region)

    def _table(self, table_name: str) -> Any:
        return self._resource.Table(table_name)

    async def get_item(
        self, table_name: str, key: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Return a single item by primary key (partition and sort key), or ``None`` if not found."""
        loop = asyncio.get_running_loop()
        table = self._table(table_name)
        try:
            response = await loop.run_in_executor(
                None, partial(table.get_item, Key=key)
            )
            return response.get("Item")
        except ClientError:
            logger.exception(f"DynamoDB get_item failed for table={table_name} key={key}")
            raise

    async def put_item(self, table_name: str, item: dict[str, Any]) -> None:
        """Write (or overwrite) a single item."""
        loop = asyncio.get_running_loop()
        table = self._table(table_name)
        try:
            await loop.run_in_executor(None, partial(table.put_item, Item=item))
        except ClientError:
            logger.exception(f"DynamoDB put_item failed for table={table_name}")
            raise

    async def delete_item(self, table_name: str, key: dict[str, Any]) -> None:
        """Delete a single item by primary key."""
        loop = asyncio.get_running_loop()
        table = self._table(table_name)
        try:
            await loop.run_in_executor(None, partial(table.delete_item, Key=key))
        except ClientError:
            logger.exception(f"DynamoDB delete_item failed for table={table_name} key={key}")
            raise

    async def query(
        self,
        table_name: str,
        key_condition: ConditionBase,
        *,
        index_name: str | None = None,
        filter_expression: ConditionBase | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query items using a key condition expression. Fetch multiple parition keys and/or sort keys, with optional filtering and pagination
        """
        loop = asyncio.get_running_loop()
        table = self._table(table_name)
        kwargs: dict[str, Any] = {"KeyConditionExpression": key_condition} #required argument for query, defines the condition for the partition key (and optionally sort key) to identify which items to return, must be provided using boto3's condition expression syntax
        if index_name is not None:
            kwargs["IndexName"] = index_name
        if filter_expression is not None:
            kwargs["FilterExpression"] = filter_expression #After query returns, returns all items with partition key defined (multiple index keys can have same partition key but different sort keys) and then applies filter expression to filter down results to only those matching filter expression, if provided
        if limit is not None:
            kwargs["Limit"] = limit
        try:
            response = await loop.run_in_executor(None, partial(table.query, **kwargs))
            return response.get("Items", [])
        except ClientError:
            logger.exception(f"DynamoDB query failed for table={table_name}")
            raise
