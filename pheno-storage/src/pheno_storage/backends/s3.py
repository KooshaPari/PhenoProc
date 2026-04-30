"""
AWS S3 storage backend implementation.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from .base import StorageBackend

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class S3StorageBackend(StorageBackend):
    """
    AWS S3-based storage backend.
    """

    def __init__(
        self,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str = "us-east-1",
        endpoint_url: str | None = None,
    ):
        """Initialize S3 storage backend.

        Args:
            aws_access_key_id: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret key (defaults to AWS_SECRET_ACCESS_KEY env var)
            region_name: AWS region name (default: us-east-1)
            endpoint_url: Custom S3 endpoint for S3-compatible services (optional)
        """
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self._client = None

    def _get_client(self):
        """
        Get boto3 S3 client, lazy-loading if needed.
        """
        if self._client is None:
            try:
                import boto3

                self._client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name,
                    endpoint_url=self.endpoint_url,
                )
            except ImportError:
                raise ImportError("boto3 not installed. Install with: pip install boto3")
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
        Upload a file to S3.
        """
        client = self._get_client()

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = metadata

        try:
            import io

            client.upload_fileobj(
                io.BytesIO(data), bucket, path, ExtraArgs=extra_args if extra_args else None,
            )
            return self.get_public_url(bucket, path)
        except Exception as e:
            raise RuntimeError(f"Failed to upload to S3: {e}")

    async def download(self, bucket: str, path: str) -> bytes:
        """
        Download a file from S3.
        """
        client = self._get_client()

        try:
            import io

            buffer = io.BytesIO()
            client.download_fileobj(bucket, path, buffer)
            return buffer.getvalue()
        except Exception as e:
            raise RuntimeError(f"Failed to download from S3: {e}")

    async def delete(self, bucket: str, path: str) -> bool:
        """
        Delete a file from S3.
        """
        client = self._get_client()

        try:
            client.delete_object(Bucket=bucket, Key=path)
            return True
        except Exception:
            return False

    async def exists(self, bucket: str, path: str) -> bool:
        """
        Check if a file exists in S3.
        """
        client = self._get_client()

        try:
            client.head_object(Bucket=bucket, Key=path)
            return True
        except Exception:
            return False

    async def list_files(
        self, bucket: str, prefix: str | None = None, limit: int | None = None,
    ) -> list[dict[str, any]]:
        """
        List files in an S3 bucket.
        """
        client = self._get_client()

        try:
            kwargs = {"Bucket": bucket}
            if prefix:
                kwargs["Prefix"] = prefix
            if limit:
                kwargs["MaxKeys"] = limit

            response = client.list_objects_v2(**kwargs)

            files = []
            for obj in response.get("Contents", []):
                files.append(
                    {
                        "name": obj["Key"],
                        "size": obj["Size"],
                        "modified": obj["LastModified"].timestamp(),
                        "etag": obj["ETag"],
                    },
                )

            return files
        except Exception as e:
            raise RuntimeError(f"Failed to list S3 objects: {e}")

    def get_public_url(self, bucket: str, path: str) -> str:
        """
        Get public URL for a file in S3.
        """
        if self.endpoint_url:
            return f"{self.endpoint_url}/{bucket}/{path}"
        return f"https://{bucket}.s3.{self.region_name}.amazonaws.com/{path}"

    async def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """
        Get a signed URL with temporary access.
        """
        client = self._get_client()

        try:
            return client.generate_presigned_url(
                "get_object", Params={"Bucket": bucket, "Key": path}, ExpiresIn=expires_in,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}")

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
        Upload file in chunks via streaming (multipart upload).
        """
        client = self._get_client()

        try:
            # Initiate multipart upload
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = metadata

            response = client.create_multipart_upload(Bucket=bucket, Key=path, **extra_args)
            upload_id = response["UploadId"]

            parts = []
            part_number = 1

            async for chunk in chunk_iterator:
                part_response = client.upload_part(
                    Bucket=bucket, Key=path, PartNumber=part_number, UploadId=upload_id, Body=chunk,
                )
                parts.append({"PartNumber": part_number, "ETag": part_response["ETag"]})
                part_number += 1

            # Complete multipart upload
            client.complete_multipart_upload(
                Bucket=bucket, Key=path, UploadId=upload_id, MultipartUpload={"Parts": parts},
            )

            return self.get_public_url(bucket, path)
        except Exception as e:
            # Abort multipart upload on error
            if "upload_id" in locals():
                client.abort_multipart_upload(Bucket=bucket, Key=path, UploadId=upload_id)
            raise RuntimeError(f"Failed to stream upload to S3: {e}")

    async def stream_download(
        self, bucket: str, path: str, chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """
        Download file in chunks via streaming.
        """
        client = self._get_client()

        try:
            response = client.get_object(Bucket=bucket, Key=path)
            stream = response["Body"]

            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            raise RuntimeError(f"Failed to stream download from S3: {e}")
