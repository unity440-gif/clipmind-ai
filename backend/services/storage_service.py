"""
Cloud storage service using Cloudflare R2 (S3-compatible).
Wraps upload/download/delete operations so the rest of the app doesn't
need to know or care that files live in R2 instead of local disk.
Files persist across every deploy/restart, unlike local container disk.
"""

import boto3
from botocore.client import Config
from boto3.s3.transfer import TransferConfig

from config.settings import settings

_client = None

# Force simple single-part uploads instead of multipart — some R2 API
# tokens have a permissions bug specifically on CreateMultipartUpload
# even when otherwise correctly scoped for read/write.
_UPLOAD_CONFIG = TransferConfig(multipart_threshold=1024 * 1024 * 1024 * 5)  # 5GB


def get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _client


def upload_file(local_path: str, key: str) -> str:
    """
    Uploads a local file to R2 under the given key (like a filename/path
    inside the bucket). Returns that same key, which is what we'll store
    in the database as the file's "storage_path" going forward.
    """
    client = get_client()
    client.upload_file(local_path, settings.R2_BUCKET_NAME, key, Config=_UPLOAD_CONFIG)
    return key


def download_file(key: str, local_path: str) -> None:
    """Downloads a file from R2 to a local path, for tools like FFmpeg/Whisper that need a real file on disk to work with."""
    client = get_client()
    client.download_file(settings.R2_BUCKET_NAME, key, local_path)


def delete_file(key: str) -> None:
    client = get_client()
    client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)


def file_exists(key: str) -> bool:
    client = get_client()
    try:
        client.head_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        return True
    except client.exceptions.ClientError:
        return False


def get_public_url(key: str) -> str:
    """
    Generates a time-limited signed URL for reading a file directly —
    used so the browser can stream video clips straight from R2
    instead of routing through your backend.
    """
    client = get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key},
        ExpiresIn=3600,  # 1 hour
    )