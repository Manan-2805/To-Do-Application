import asyncio
import os
import uuid

from src.core.config import settings
from src.core.exceptions import StorageException
from src.services.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Storage provider saving files to the local file system."""

    def __init__(self, base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _save_file_sync(self, file_name: str, contents: bytes) -> str:
        # Generate a unique prefix to avoid filename collisions
        unique_name = f"{uuid.uuid4()}_{file_name}"
        file_path = os.path.join(self.base_dir, unique_name)

        with open(file_path, "wb") as f:
            f.write(contents)

        return file_path

    def _get_file_sync(self, file_path: str) -> bytes:
        if not os.path.exists(file_path):
            raise StorageException(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            return f.read()

    def _delete_file_sync(self, file_path: str) -> None:
        if os.path.exists(file_path):
            os.remove(file_path)

    async def save_file(self, file_name: str, contents: bytes) -> str:
        """Asynchronously save file to the local directory."""
        try:
            return await asyncio.to_thread(self._save_file_sync, file_name, contents)
        except Exception as e:
            raise StorageException(f"Failed to save local file: {e!s}") from e

    async def get_file(self, file_path: str) -> bytes:
        """Asynchronously retrieve local file contents."""
        try:
            return await asyncio.to_thread(self._get_file_sync, file_path)
        except Exception as e:
            raise StorageException(f"Failed to read local file: {e!s}") from e

    async def delete_file(self, file_path: str) -> None:
        """Asynchronously delete local file."""
        try:
            await asyncio.to_thread(self._delete_file_sync, file_path)
        except Exception as e:
            raise StorageException(f"Failed to delete local file: {e!s}") from e

    async def check_health(self) -> bool:
        """Check if local storage directory is writable."""
        try:
            test_file = os.path.join(self.base_dir, f".health_{uuid.uuid4()}")

            def test_write_and_delete() -> None:
                with open(test_file, "w") as f:
                    f.write("health_check")
                os.remove(test_file)

            await asyncio.to_thread(test_write_and_delete)
            return True
        except Exception:
            return False
