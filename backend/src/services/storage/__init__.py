from src.core.config import settings
from src.services.storage.base import StorageProvider
from src.services.storage.local_provider import LocalStorageProvider
from src.services.storage.s3_provider import S3StorageProvider


_storage_provider: StorageProvider | None = None


def get_storage_provider() -> StorageProvider:
    """Factory function returning the configured storage provider instance."""
    global _storage_provider
    if _storage_provider is None:
        if settings.STORAGE_PROVIDER == "s3":
            _storage_provider = S3StorageProvider()
        else:
            _storage_provider = LocalStorageProvider()
    return _storage_provider
