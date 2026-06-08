import os
from unittest.mock import patch

import pytest

from src.core.exceptions import StorageException
from src.services.storage.local_provider import LocalStorageProvider


@pytest.mark.asyncio
async def test_local_storage_provider_lifecycle():
    """Test LocalStorageProvider standard CRUD operation flow and health checks."""
    provider = LocalStorageProvider(base_dir="./test_uploads")

    # Save
    file_path = await provider.save_file("test.txt", b"hello world")
    assert os.path.exists(file_path)

    # Get
    content = await provider.get_file(file_path)
    assert content == b"hello world"

    # Get non-existent
    with pytest.raises(StorageException):
        await provider.get_file("non_existent_file.txt")

    # Check health
    health_ok = await provider.check_health()
    assert health_ok is True

    # Delete
    await provider.delete_file(file_path)
    assert not os.path.exists(file_path)

    # Clean up test directory
    if os.path.exists("./test_uploads") and not os.listdir("./test_uploads"):
        os.rmdir("./test_uploads")


@pytest.mark.asyncio
async def test_local_storage_provider_exceptions():
    """Test LocalStorageProvider correct wrapping of filesystem exceptions."""
    provider = LocalStorageProvider(base_dir="./test_uploads")

    # Save exception
    with (
        patch(
            "src.services.storage.local_provider.LocalStorageProvider._save_file_sync",
            side_effect=Exception("Disk full"),
        ),
        pytest.raises(StorageException),
    ):
        await provider.save_file("test.txt", b"content")

    # Delete exception
    with (
        patch(
            "src.services.storage.local_provider.LocalStorageProvider._delete_file_sync",
            side_effect=Exception("Permission denied"),
        ),
        pytest.raises(StorageException),
    ):
        await provider.delete_file("some_path")

    # Check health failure
    with patch("os.path.join", side_effect=Exception("Fatal Error")):
        health_ok = await provider.check_health()
        assert health_ok is False
