"""
Abstract backend interface for storage operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..repositories.base import RepositoryBackend

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class StorageBackend(ABC):
    """Abstract interface for storage backends."""

    @abstractmethod
    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload a file.

        Args:
            bucket: Storage bucket/container name
            path: File path within bucket
            data: File data
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            Public URL or file identifier
        """

    @abstractmethod
    async def download(self, bucket: str, path: str) -> bytes:
        """Download a file.

        Args:
            bucket: Storage bucket name
            path: File path within bucket

        Returns:
            File data
        """

    @abstractmethod
    async def delete(self, bucket: str, path: str) -> bool:
        """Delete a file.

        Args:
            bucket: Storage bucket name
            path: File path within bucket

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    async def exists(self, bucket: str, path: str) -> bool:
        """Check if a file exists.

        Args:
            bucket: Storage bucket name
            path: File path within bucket

        Returns:
            True if file exists
        """

    @abstractmethod
    async def list_files(
        self,
        bucket: str,
        prefix: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, any]]:
        """List files in a bucket.

        Args:
            bucket: Storage bucket name
            prefix: Path prefix to filter by
            limit: Maximum number of files to return

        Returns:
            List of file metadata dicts
        """

    @abstractmethod
    def get_public_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file.

        Args:
            bucket: Storage bucket name
            path: File path within bucket

        Returns:
            Public URL
        """

    @abstractmethod
    async def get_signed_url(
        self, bucket: str, path: str, expires_in: int = 3600
    ) -> str:
        """Get a signed URL with temporary access.

        Args:
            bucket: Storage bucket name
            path: File path within bucket
            expires_in: Expiration time in seconds

        Returns:
            Signed URL
        """

    @abstractmethod
    async def stream_upload(
        self,
        bucket: str,
        path: str,
        chunk_iterator: AsyncIterator[bytes],
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload file in chunks via streaming.

        Args:
            bucket: Storage bucket name
            path: File path within bucket
            chunk_iterator: Async iterator of file chunks
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            Public URL or file identifier
        """

    @abstractmethod
    async def stream_download(
        self,
        bucket: str,
        path: str,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """Download file in chunks via streaming.

        Args:
            bucket: Storage bucket name
            path: File path within bucket
            chunk_size: Size of each chunk in bytes

        Yields:
            File data chunks
        """


__all__ = ["RepositoryBackend", "StorageBackend"]
