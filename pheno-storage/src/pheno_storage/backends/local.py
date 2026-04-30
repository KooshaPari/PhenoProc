"""
Local filesystem storage backend implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

from .base import StorageBackend

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem-based storage backend.
    """

    def __init__(self, base_path: str = "./storage"):
        """Initialize local storage backend.

        Args:
            base_path: Base directory for storage (default: ./storage)
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, bucket: str, path: str) -> Path:
        """
        Get full filesystem path for a bucket/path combination.
        """
        full_path = self.base_path / bucket / path
        # Ensure path is within base_path (security check)
        if not str(full_path.resolve()).startswith(str(self.base_path)):
            raise ValueError(f"Path traversal detected: {path}")
        return full_path

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
        Upload a file to local storage.
        """
        full_path = self._get_full_path(bucket, path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)

        # Store metadata separately if provided
        if metadata or content_type:
            meta = metadata or {}
            if content_type:
                meta["content-type"] = content_type

            meta_path = full_path.with_suffix(full_path.suffix + ".meta")
            async with aiofiles.open(meta_path, "w") as f:
                import json

                await f.write(json.dumps(meta))

        return self.get_public_url(bucket, path)

    async def download(self, bucket: str, path: str) -> bytes:
        """
        Download a file from local storage.
        """
        full_path = self._get_full_path(bucket, path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {bucket}/{path}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, bucket: str, path: str) -> bool:
        """
        Delete a file from local storage.
        """
        try:
            full_path = self._get_full_path(bucket, path)

            if full_path.exists():
                full_path.unlink()

                # Also delete metadata if it exists
                meta_path = full_path.with_suffix(full_path.suffix + ".meta")
                if meta_path.exists():
                    meta_path.unlink()

                return True
            return False
        except Exception:
            return False

    async def exists(self, bucket: str, path: str) -> bool:
        """
        Check if a file exists in local storage.
        """
        full_path = self._get_full_path(bucket, path)
        return full_path.exists()

    async def list_files(
        self, bucket: str, prefix: str | None = None, limit: int | None = None,
    ) -> list[dict[str, any]]:
        """
        List files in a local bucket.
        """
        bucket_path = self.base_path / bucket

        if not bucket_path.exists():
            return []

        files = []
        pattern = f"{prefix}*" if prefix else "*"

        for file_path in bucket_path.rglob(pattern):
            if file_path.is_file() and file_path.suffix != ".meta":
                relative_path = str(file_path.relative_to(bucket_path))
                files.append(
                    {
                        "name": relative_path,
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime,
                    },
                )

                if limit and len(files) >= limit:
                    break

        return files

    def get_public_url(self, bucket: str, path: str) -> str:
        """Get public URL for a local file (file:// URL)."""
        full_path = self._get_full_path(bucket, path)
        return f"file://{full_path}"

    async def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """
        Get a signed URL (same as public URL for local storage).
        """
        return self.get_public_url(bucket, path)

    async def stream_upload(
        self,
        bucket: str,
        path: str,
        chunk_iterator: AsyncIterator[bytes],
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload file in chunks via streaming.
        """
        full_path = self._get_full_path(bucket, path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            async for chunk in chunk_iterator:
                await f.write(chunk)

        # Store metadata
        if metadata or content_type:
            meta = metadata or {}
            if content_type:
                meta["content-type"] = content_type

            meta_path = full_path.with_suffix(full_path.suffix + ".meta")
            async with aiofiles.open(meta_path, "w") as f:
                import json

                await f.write(json.dumps(meta))

        return self.get_public_url(bucket, path)

    async def stream_download(
        self, bucket: str, path: str, chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """
        Download file in chunks via streaming.
        """
        full_path = self._get_full_path(bucket, path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {bucket}/{path}")

        async with aiofiles.open(full_path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
