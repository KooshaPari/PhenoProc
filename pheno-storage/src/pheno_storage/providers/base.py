"""
Base storage provider interface.
"""

from abc import ABC, abstractmethod

from pheno.storage.core.file import StoredFile


class StorageProvider(ABC):
    """Base storage provider interface.

    Example:
        provider = S3StorageProvider(bucket="my-bucket")

        # Upload file
        file = await provider.upload("path/to/file.txt", data)

        # Download file
        data = await provider.download("path/to/file.txt")

        # Delete file
        await provider.delete("path/to/file.txt")
    """

    @abstractmethod
    async def upload(
        self,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict | None = None,
    ) -> StoredFile:
        """
        Upload file.
        """

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """
        Download file.
        """

    @abstractmethod
    async def delete(self, path: str):
        """
        Delete file.
        """

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        Check if file exists.
        """

    @abstractmethod
    async def get_url(
        self,
        path: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Get presigned URL.
        """


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider.

    Example:
        provider = LocalStorageProvider(base_path="./storage")
        file = await provider.upload("test.txt", b"Hello")
    """

    def __init__(self, base_path: str = "./storage"):
        from pathlib import Path

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, path: str):
        """
        Get full file path.
        """
        return self.base_path / path

    async def upload(
        self,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict | None = None,
    ) -> StoredFile:
        """
        Upload file to local filesystem.
        """
        file_path = self._get_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_bytes(data)

        return StoredFile(
            path=path,
            size=len(data),
            content_type=content_type,
            url=str(file_path),
            metadata=metadata,
        )

    async def download(self, path: str) -> bytes:
        """
        Download file from local filesystem.
        """
        file_path = self._get_path(path)
        return file_path.read_bytes()

    async def delete(self, path: str):
        """
        Delete file from local filesystem.
        """
        file_path = self._get_path(path)
        if file_path.exists():
            file_path.unlink()

    async def exists(self, path: str) -> bool:
        """
        Check if file exists.
        """
        return self._get_path(path).exists()

    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        """
        Get file URL (local file path).
        """
        return str(self._get_path(path))


class InMemoryStorageProvider(StorageProvider):
    """
    In-memory storage provider for testing.
    """

    def __init__(self):
        self._files: dict = {}

    async def upload(
        self,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict | None = None,
    ) -> StoredFile:
        """
        Upload file to memory.
        """
        self._files[path] = (data, content_type, metadata)

        return StoredFile(
            path=path,
            size=len(data),
            content_type=content_type,
            metadata=metadata,
        )

    async def download(self, path: str) -> bytes:
        """
        Download file from memory.
        """
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path][0]

    async def delete(self, path: str):
        """
        Delete file from memory.
        """
        self._files.pop(path, None)

    async def exists(self, path: str) -> bool:
        """
        Check if file exists.
        """
        return path in self._files

    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        """
        Get file URL (memory://path).
        """
        return f"memory://{path}"
