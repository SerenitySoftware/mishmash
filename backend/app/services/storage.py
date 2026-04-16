import uuid

import boto3
from botocore.config import Config

from app.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def generate_upload_key(dataset_id: uuid.UUID, version: int, filename: str) -> str:
    return f"datasets/{dataset_id}/v{version}/{filename}"


def generate_result_key(run_id: uuid.UUID, filename: str) -> str:
    return f"results/{run_id}/{filename}"


def create_presigned_upload_url(
    key: str,
    content_type: str = "application/octet-stream",
    expires_in: int = 900,
) -> str:
    client = get_s3_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_datasets_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
    return url


def create_presigned_download_url(
    bucket: str,
    key: str,
    expires_in: int = 3600,
) -> str:
    client = get_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )
    return url


def download_file(bucket: str, key: str, local_path: str) -> None:
    client = get_s3_client()
    client.download_file(bucket, key, local_path)


def upload_file(local_path: str, bucket: str, key: str) -> None:
    client = get_s3_client()
    client.upload_file(local_path, bucket, key)
