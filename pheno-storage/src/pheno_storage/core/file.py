"""
File representation.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class StoredFile:
    """
    Stored file metadata.
    """

    path: str
    size: int
    content_type: str
    url: str | None = None
    etag: str | None = None
    created_at: datetime | None = None
    metadata: dict | None = None
