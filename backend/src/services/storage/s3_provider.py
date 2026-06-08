import logging

from src.core.exceptions import StorageException
from src.services.storage.base import StorageProvider


logger = logging.getLogger("todosphere.storage.s3")


class S3StorageProvider(StorageProvider):
    """Stub implementation for S3 storage provider. Prepared for future cloud migrations."""

    def __init__(self):
        logger.warning(
            "S3StorageProvider is initialized as a STUB. AWS uploads are not active."
        )

    async def save_file(self, file_name: str, contents: bytes) -> str:
        """Stub save_file."""
        logger.warning(
            f"S3StorageProvider.save_file called for {file_name} (STUB). File not persisted to cloud."
        )
        raise StorageException(
            "S3StorageProvider is currently a stub and not active. Use LocalStorageProvider."
        )

    async def get_file(self, file_path: str) -> bytes:
        """Stub get_file."""
        logger.warning(f"S3StorageProvider.get_file called for {file_path} (STUB).")
        raise StorageException(
            "S3StorageProvider is currently a stub and not active. Use LocalStorageProvider."
        )

    async def delete_file(self, file_path: str) -> None:
        """Stub delete_file."""
        logger.warning(f"S3StorageProvider.delete_file called for {file_path} (STUB).")

    async def check_health(self) -> bool:
        """Stub check_health."""
        logger.warning("S3StorageProvider.check_health called (STUB). Returning False.")
        return False
