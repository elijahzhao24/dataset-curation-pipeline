from __future__ import annotations

from pathlib import Path


def upload_to_s3(s3_client, local_path: str | Path, bucket: str, key: str) -> None:
    s3_client.upload_file(str(local_path), bucket, key)


def make_s3_key(local_path: str | Path, prefix: str) -> str:
    name = Path(local_path).name
    return f"{prefix.rstrip('/')}/{name}"
