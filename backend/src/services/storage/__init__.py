from src.core.config import settings
from src.services.storage.base import StorageProvider
from src.services.storage.local_provider import LocalStorageProvider
from src.services.storage.s3_provider import S3StorageProvider


def get_storage_provider() -> StorageProvider:
    """Factory function returning the configured storage provider instance."""
    if settings.STORAGE_PROVIDER == "s3":
        return S3StorageProvider()
    return LocalStorageProvider()
