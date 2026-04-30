"""
Universal storage client.
"""

from pheno.storage.core.file import StoredFile
from pheno.storage.providers.base import StorageProvider


class StorageClient:
    """Universal storage client.

    Provides unified interface across storage providers.

    Example:
        # Local storage
        client = StorageClient(LocalStorageProvider())

        # S3 storage
        client = StorageClient(S3StorageProvider(bucket="my-bucket"))

        # Upload file
        file = await client.upload("test.txt", b"Hello World")

        # Download file
        data = await client.download("test.txt")

        # Get presigned URL
        url = await client.get_url("test.txt", expires_in=3600)
    """

    def __init__(self, provider: StorageProvider):
        self.provider = provider

    async def upload(
        self,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict | None = None,
    ) -> StoredFile:
        """Upload file.

        Args:
            path: File path
            data: File data
            content_type: MIME type
            metadata: Optional metadata

        Returns:
            StoredFile object
        """
        return await self.provider.upload(
            path=path,
            data=data,
            content_type=content_type,
            metadata=metadata,
        )

    async def download(self, path: str) -> bytes:
        """Download file.

        Args:
            path: File path

        Returns:
            File data
        """
        return await self.provider.download(path)

    async def delete(self, path: str):
        """Delete file.

        Args:
            path: File path
        """
        await self.provider.delete(path)

    async def exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: File path

        Returns:
            True if exists
        """
        return await self.provider.exists(path)

    async def get_url(self, path: str, expires_in: int = 3600) -> str:
        """Get presigned URL.

        Args:
            path: File path
            expires_in: URL expiration in seconds

        Returns:
            Presigned URL
        """
        return await self.provider.get_url(path, expires_in)
