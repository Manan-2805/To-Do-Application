import abc


class StorageProvider(abc.ABC):
    """Abstract base class defining storage capabilities for attachments."""

    @abc.abstractmethod
    async def save_file(self, file_name: str, contents: bytes) -> str:
        """Save a file and return its path or URI."""
        pass

    @abc.abstractmethod
    async def get_file(self, file_path: str) -> bytes:
        """Retrieve the binary contents of a file."""
        pass

    @abc.abstractmethod
    async def delete_file(self, file_path: str) -> None:
        """Delete a file from storage."""
        pass

    @abc.abstractmethod
    async def check_health(self) -> bool:
        """Validate if the storage backend is reachable and writable."""
        pass


class StorageException(Exception):
    pass
