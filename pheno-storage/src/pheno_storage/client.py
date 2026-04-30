"""
Main Storage client interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .backends.local import LocalStorageBackend
from .backends.s3 import S3StorageBackend
from .backends.supabase import SupabaseStorageBackend

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from .backends.base import StorageBackend


class Storage:
    """
    Universal storage client with pluggable backends.
    """

    def __init__(self, backend: StorageBackend, default_bucket: str | None = None):
        """Initialize storage client.

        Args:
            backend: Storage backend implementation
            default_bucket: Default bucket to use (optional)
        """
        self.backend = backend
        self.default_bucket = default_bucket

    @classmethod
    def supabase(
        cls, client=None, base_url: str | None = None, default_bucket: str | None = None,
    ) -> Storage:
        """Create a storage client with Supabase backend.

        Args:
            client: Supabase client instance (optional)
            base_url: Supabase base URL (optional)
            default_bucket: Default bucket name

        Returns:
            Storage instance
        """
        backend = SupabaseStorageBackend(client=client, base_url=base_url)
        return cls(backend=backend, default_bucket=default_bucket)

    @classmethod
    def local(cls, base_path: str = "./storage", default_bucket: str | None = None) -> Storage:
        """Create a storage client with local filesystem backend.

        Args:
            base_path: Base directory for storage
            default_bucket: Default bucket name

        Returns:
            Storage instance
        """
        backend = LocalStorageBackend(base_path=base_path)
        return cls(backend=backend, default_bucket=default_bucket)

    @classmethod
    def s3(
        cls,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str = "us-east-1",
        endpoint_url: str | None = None,
        default_bucket: str | None = None,
    ) -> Storage:
        """Create a storage client with S3 backend.

        Args:
            aws_access_key_id: AWS access key (optional, uses env var)
            aws_secret_access_key: AWS secret key (optional, uses env var)
            region_name: AWS region (default: us-east-1)
            endpoint_url: Custom S3 endpoint for S3-compatible services
            default_bucket: Default bucket name

        Returns:
            Storage instance
        """
        backend = S3StorageBackend(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            endpoint_url=endpoint_url,
        )
        return cls(backend=backend, default_bucket=default_bucket)

    def _get_bucket(self, bucket: str | None) -> str:
        """
        Get bucket name, falling back to default.
        """
        if bucket:
            return bucket
        if self.default_bucket:
            return self.default_bucket
        raise ValueError("No bucket specified and no default bucket set")

    async def upload(
        self,
        path: str,
        data: bytes,
        *,
        bucket: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload a file.

        Args:
            path: File path within bucket
            data: File data
            bucket: Bucket name (uses default if not specified)
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            Public URL or file identifier
        """
        bucket_name = self._get_bucket(bucket)
        return await self.backend.upload(
            bucket_name, path, data, content_type=content_type, metadata=metadata,
        )

    async def download(self, path: str, *, bucket: str | None = None) -> bytes:
        """Download a file.

        Args:
            path: File path within bucket
            bucket: Bucket name (uses default if not specified)

        Returns:
            File data
        """
        bucket_name = self._get_bucket(bucket)
        return await self.backend.download(bucket_name, path)

    async def delete(self, path: str, *, bucket: str | None = None) -> bool:
        """Delete a file.

        Args:
            path: File path within bucket
            bucket: Bucket name (uses default if not specified)

        Returns:
            True if deleted, False if not found
        """
        bucket_name = self._get_bucket(bucket)
        return await self.backend.delete(bucket_name, path)

    async def exists(self, path: str, *, bucket: str | None = None) -> bool:
        """Check if a file exists.

        Args:
            path: File path within bucket
            bucket: Bucket name (uses default if not specified)

        Returns:
            True if file exists
        """
        bucket_name = self._get_bucket(bucket)
        return await self.backend.exists(bucket_name, path)

    async def list(
        self, prefix: str | None = None, *, bucket: str | None = None, limit: int | None = None,
    ) -> list[dict[str, any]]:
        """List files in a bucket.

        Args:
            prefix: Path prefix to filter by
            bucket: Bucket name (uses default if not specified)
            limit: Maximum number of files to return

        Returns:
            List of file metadata dicts
        """
        bucket_name = self._get_bucket(bucket)
        return await self.backend.list_files(bucket_name, prefix=prefix, limit=limit)

    def get_public_url(self, path: str, *, bucket: str | None = None) -> str:
        """Get public URL for a file.

        Args:
            path: File path within bucket
            bucket: Bucket name (uses default if not specified)

        Returns:
            Public URL
        """
        bucket_name = self._get_bucket(bucket)
        return self.backend.get_public_url(bucket_name, path)

    async def get_signed_url(
        self, path: str, *, bucket: str | None = None, expires_in: int = 3600,
    ) -> str:
        """Get a signed URL with temporary access.

        Args:
            path: File path within bucket
            bucket: Bucket name (uses default if not specified)
            expires_in: Expiration time in seconds

        Returns:
            Signed URL
        """
        bucket_name = self._get_bucket(bucket)
        return await self.backend.get_signed_url(bucket_name, path, expires_in=expires_in)

    async def stream_upload(
        self,
        path: str,
        chunk_iterator: AsyncIterator[bytes],
        *,
        bucket: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload file in chunks via streaming.

        Args:
            path: File path within bucket
            chunk_iterator: Async iterator of file chunks
            bucket: Bucket name (uses default if not specified)
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            Public URL or file identifier
        """
        bucket_name = self._get_bucket(bucket)
        return await self.backend.stream_upload(
            bucket_name, path, chunk_iterator, content_type=content_type, metadata=metadata,
        )

    async def stream_download(
        self, path: str, *, bucket: str | None = None, chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """Download file in chunks via streaming.

        Args:
            path: File path within bucket
            bucket: Bucket name (uses default if not specified)
            chunk_size: Size of each chunk in bytes

        Yields:
            File data chunks
        """
        bucket_name = self._get_bucket(bucket)
        async for chunk in self.backend.stream_download(bucket_name, path, chunk_size=chunk_size):
            yield chunk
