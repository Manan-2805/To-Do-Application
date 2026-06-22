import logging
from typing import Any

from aiobotocore.session import AioSession

from src.core.config import settings
from src.core.exceptions import StorageException
from src.services.storage.base import StorageProvider


logger = logging.getLogger("todosphere.storage.s3")


class S3StorageProvider(StorageProvider):
    """Async S3 storage provider backed by aiobotocore.

    Works with both LocalStack (when S3_ENDPOINT_URL is set) and real AWS S3
    (when S3_ENDPOINT_URL is empty). The caller switches between them purely via
    environment variables — no code changes required.
    """

    def __init__(self) -> None:
        self._session = AioSession()
        self._bucket = settings.S3_BUCKET_NAME
        self._access_key = settings.S3_ACCESS_KEY
        self._secret_key = settings.S3_SECRET_KEY
        self._endpoint_url: str | None = settings.S3_ENDPOINT_URL or None
        logger.info(
            "S3StorageProvider initialised. bucket=%s endpoint=%s",
            self._bucket,
            self._endpoint_url or "aws-default",
        )

    def _client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "region_name": "us-east-1",
            "aws_access_key_id": self._access_key,
            "aws_secret_access_key": self._secret_key,
        }
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        return kwargs

    async def save_file(self, file_name: str, contents: bytes) -> str:
        """Upload bytes to S3 and return the object key."""
        try:
            async with self._session.create_client("s3", **self._client_kwargs()) as client:
                await client.put_object(
                    Bucket=self._bucket,
                    Key=file_name,
                    Body=contents,
                )
            logger.debug("Uploaded file to S3. key=%s size=%d", file_name, len(contents))
            return file_name
        except Exception as exc:
            logger.error("S3 upload failed. key=%s error=%s", file_name, exc)
            raise StorageException(f"Failed to upload file '{file_name}' to S3: {exc}") from exc

    async def get_file(self, file_path: str) -> bytes:
        """Download an object from S3 and return its bytes."""
        try:
            async with self._session.create_client("s3", **self._client_kwargs()) as client:
                response = await client.get_object(Bucket=self._bucket, Key=file_path)
                async with response["Body"] as stream:
                    data: bytes = await stream.read()
            logger.debug("Downloaded file from S3. key=%s size=%d", file_path, len(data))
            return data
        except Exception as exc:
            logger.error("S3 download failed. key=%s error=%s", file_path, exc)
            raise StorageException(f"Failed to download file '{file_path}' from S3: {exc}") from exc

    async def delete_file(self, file_path: str) -> None:
        """Delete an object from S3."""
        try:
            async with self._session.create_client("s3", **self._client_kwargs()) as client:
                await client.delete_object(Bucket=self._bucket, Key=file_path)
            logger.debug("Deleted file from S3. key=%s", file_path)
        except Exception as exc:
            logger.error("S3 delete failed. key=%s error=%s", file_path, exc)
            raise StorageException(f"Failed to delete file '{file_path}' from S3: {exc}") from exc

    async def check_health(self) -> bool:
        """Return True if the configured S3 bucket is reachable."""
        try:
            async with self._session.create_client("s3", **self._client_kwargs()) as client:
                await client.head_bucket(Bucket=self._bucket)
            return True
        except Exception as exc:
            logger.warning("S3 health check failed. bucket=%s error=%s", self._bucket, exc)
            return False
