"""
pheno.storage - Multi-provider cloud storage

Provides unified storage interface for S3, GCS, Azure Blob, and local storage.

Migrated from storage-kit into pheno namespace.

Usage:
    from pheno.storage import StorageClient, StorageProvider

    # Create S3 client
    client = StorageClient(
        provider="s3",
        bucket="my-bucket",
        region="us-east-1"
    )

    # Upload file
    await client.upload("local/file.txt", "remote/file.txt")

    # Download file
    await client.download("remote/file.txt", "local/file.txt")

    # List files
    files = await client.list("prefix/")
"""

from __future__ import annotations

from .core.client import StorageClient
from .core.file import StoredFile
from .providers.base import StorageProvider

__version__ = "0.1.0"

__all__ = [
    "StorageClient",
    "StorageProvider",
    "StoredFile",
]
