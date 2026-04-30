"""
Supabase storage backend implementation.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from .base import StorageBackend

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class SupabaseStorageBackend(StorageBackend):
    """
    Supabase-based storage backend.
    """

    def __init__(self, client=None, base_url: str | None = None):
        """Initialize Supabase storage backend.

        Args:
            client: Supabase client instance (optional, will auto-initialize)
            base_url: Base URL for storage (defaults to NEXT_PUBLIC_SUPABASE_URL env var)
        """
        self._client = client
        self._base_url = base_url or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        if not self._base_url:
            raise ValueError("base_url or NEXT_PUBLIC_SUPABASE_URL must be set")

    def _get_client(self):
        """
        Get Supabase client, lazy-loading if needed.
        """
        if self._client is None:
            # Attempt to import and initialize
            try:
                from supabase import create_client

                url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
                key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
                if not url or not key:
                    raise ValueError(
                        "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY",
                    )
                self._client = create_client(url, key)
            except ImportError:
                raise ImportError("supabase-py not installed. Install with: pip install supabase")
        return self._client

    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload a file to Supabase storage.
        """
        client = self._get_client()
        storage = client.storage.from_(bucket)

        file_options = {}
        if content_type:
            file_options["content-type"] = content_type
        if metadata:
            file_options.update(metadata)

        result = storage.upload(path, data, file_options=file_options)

        if hasattr(result, "error") and result.error:
            raise RuntimeError(f"Failed to upload file: {result.error}")

        return self.get_public_url(bucket, path)

    async def download(self, bucket: str, path: str) -> bytes:
        """
        Download a file from Supabase storage.
        """
        client = self._get_client()
        storage = client.storage.from_(bucket)

        result = storage.download(path)

        if hasattr(result, "error") and result.error:
            raise RuntimeError(f"Failed to download file: {result.error}")

        return result

    async def delete(self, bucket: str, path: str) -> bool:
        """
        Delete a file from Supabase storage.
        """
        try:
            client = self._get_client()
            storage = client.storage.from_(bucket)

            result = storage.remove([path])

            return not (hasattr(result, "error") and result.error)
        except Exception:
            return False

    async def exists(self, bucket: str, path: str) -> bool:
        """
        Check if a file exists in Supabase storage.
        """
        try:
            client = self._get_client()
            storage = client.storage.from_(bucket)

            # Try to list the file
            result = storage.list(path=path)
            return len(result) > 0
        except Exception:
            return False

    async def list_files(
        self, bucket: str, prefix: str | None = None, limit: int | None = None,
    ) -> list[dict[str, any]]:
        """
        List files in a Supabase bucket.
        """
        client = self._get_client()
        storage = client.storage.from_(bucket)

        result = storage.list(path=prefix or "", limit=limit)

        if hasattr(result, "error") and result.error:
            raise RuntimeError(f"Failed to list files: {result.error}")

        return result

    def get_public_url(self, bucket: str, path: str) -> str:
        """
        Get public URL for a file in Supabase storage.
        """
        return f"{self._base_url}/storage/v1/object/public/{bucket}/{path}"

    async def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """
        Get a signed URL with temporary access.
        """
        client = self._get_client()
        storage = client.storage.from_(bucket)

        result = storage.create_signed_url(path, expires_in)

        if hasattr(result, "error") and result.error:
            raise RuntimeError(f"Failed to create signed URL: {result.error}")

        return result.get("signedURL", "")

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

        Note: Supabase doesn't have native streaming upload, so we buffer chunks.
        """
        # Buffer all chunks
        chunks = []
        async for chunk in chunk_iterator:
            chunks.append(chunk)

        data = b"".join(chunks)
        return await self.upload(bucket, path, data, content_type=content_type, metadata=metadata)

    async def stream_download(
        self, bucket: str, path: str, chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """
        Download file in chunks via streaming.
        """
        data = await self.download(bucket, path)

        # Yield chunks
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]
