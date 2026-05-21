import os
import shutil
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)

class StorageProvider(ABC):
    @abstractmethod
    def upload_file(self, local_path: str, remote_filename: str) -> Optional[str]:
        """Uploads a local file to storage and returns URI or path."""
        pass

    @abstractmethod
    def download_file(self, remote_filename: str, local_path: str) -> bool:
        """Downloads a remote file to a local path."""
        pass

    @abstractmethod
    def delete_file(self, remote_filename: str) -> bool:
        """Deletes a file from storage."""
        pass

    @abstractmethod
    def list_files(self) -> List[str]:
        """Lists files in the storage."""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)

    def upload_file(self, local_path: str, remote_filename: str) -> Optional[str]:
        target_path = os.path.join(self.upload_dir, remote_filename)
        if local_path != target_path:
            shutil.copy2(local_path, target_path)
        return target_path

    def download_file(self, remote_filename: str, local_path: str) -> bool:
        source_path = os.path.join(self.upload_dir, remote_filename)
        if os.path.exists(source_path):
            if source_path != local_path:
                shutil.copy2(source_path, local_path)
            return True
        return False

    def delete_file(self, remote_filename: str) -> bool:
        file_path = os.path.join(self.upload_dir, remote_filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError as e:
                logger.error(f"LocalStorageProvider: Failed to delete {remote_filename}: {e}")
                return False
        return False

    def list_files(self) -> List[str]:
        if not os.path.exists(self.upload_dir):
            return []
        return [f for f in os.listdir(self.upload_dir) if not f.startswith(".")]


class S3StorageProvider(StorageProvider):
    def __init__(self):
        import boto3
        
        self.bucket = os.getenv("AWS_BUCKET_NAME")
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        endpoint_url = os.getenv("S3_ENDPOINT_URL")  # For Cloudflare R2 or custom S3
        region = os.getenv("AWS_REGION", "us-east-1")
        
        kwargs = {}
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if region:
            kwargs["region_name"] = region

        self.s3 = boto3.client("s3", **kwargs)
        logger.info(f"S3StorageProvider initialized with bucket: {self.bucket}")

    def upload_file(self, local_path: str, remote_filename: str) -> Optional[str]:
        try:
            self.s3.upload_file(local_path, self.bucket, remote_filename)
            return f"s3://{self.bucket}/{remote_filename}"
        except Exception as e:
            logger.error(f"S3StorageProvider: Upload failed for {remote_filename}: {e}")
            return None

    def download_file(self, remote_filename: str, local_path: str) -> bool:
        try:
            self.s3.download_file(self.bucket, remote_filename, local_path)
            return True
        except Exception as e:
            logger.error(f"S3StorageProvider: Download failed for {remote_filename}: {e}")
            return False

    def delete_file(self, remote_filename: str) -> bool:
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=remote_filename)
            return True
        except Exception as e:
            logger.error(f"S3StorageProvider: Delete failed for {remote_filename}: {e}")
            return False

    def list_files(self) -> List[str]:
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket)
            if "Contents" in response:
                return [obj["Key"] for obj in response["Contents"] if not obj["Key"].endswith(".index") and not obj["Key"] == "metadata.json"]
            return []
        except Exception as e:
            logger.error(f"S3StorageProvider: List files failed: {e}")
            return []


class SupabaseStorageProvider(StorageProvider):
    def __init__(self):
        from supabase import create_client, Client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "documents")
        self.supabase: Client = create_client(url, key)
        logger.info(f"SupabaseStorageProvider initialized with bucket: {self.bucket_name}")

    def upload_file(self, local_path: str, remote_filename: str) -> Optional[str]:
        try:
            with open(local_path, "rb") as f:
                self.supabase.storage.from_(self.bucket_name).upload(
                    path=remote_filename,
                    file=f,
                    file_options={"cache-control": "3600", "upsert": "true"}
                )
            return f"supabase://{self.bucket_name}/{remote_filename}"
        except Exception as e:
            logger.error(f"SupabaseStorageProvider: Upload failed for {remote_filename}: {e}")
            return None

    def download_file(self, remote_filename: str, local_path: str) -> bool:
        try:
            response = self.supabase.storage.from_(self.bucket_name).download(remote_filename)
            with open(local_path, "wb") as f:
                f.write(response)
            return True
        except Exception as e:
            logger.error(f"SupabaseStorageProvider: Download failed for {remote_filename}: {e}")
            return False

    def delete_file(self, remote_filename: str) -> bool:
        try:
            self.supabase.storage.from_(self.bucket_name).remove([remote_filename])
            return True
        except Exception as e:
            logger.error(f"SupabaseStorageProvider: Delete failed for {remote_filename}: {e}")
            return False

    def list_files(self) -> List[str]:
        try:
            res = self.supabase.storage.from_(self.bucket_name).list()
            return [item["name"] for item in res if not item["name"].endswith(".index") and not item["name"] == "metadata.json"]
        except Exception as e:
            logger.error(f"SupabaseStorageProvider: List files failed: {e}")
            return []


class StorageService:
    def __init__(self):
        base_path = os.getenv("BASE_PATH", "./data")
        self.local_upload_dir = os.path.join(base_path, "uploads")
        
        provider_type = os.getenv("STORAGE_PROVIDER", "local").lower().strip()
        self.provider_type = provider_type
        
        if provider_type == "s3":
            try:
                self.provider = S3StorageProvider()
            except Exception as e:
                logger.error(f"Failed to initialize S3 storage, falling back to local: {e}")
                self.provider = LocalStorageProvider(self.local_upload_dir)
                self.provider_type = "local"
        elif provider_type == "supabase":
            try:
                self.provider = SupabaseStorageProvider()
            except Exception as e:
                logger.error(f"Failed to initialize Supabase storage, falling back to local: {e}")
                self.provider = LocalStorageProvider(self.local_upload_dir)
                self.provider_type = "local"
        else:
            self.provider = LocalStorageProvider(self.local_upload_dir)

    def upload_file(self, local_path: str, remote_filename: str) -> Optional[str]:
        return self.provider.upload_file(local_path, remote_filename)

    def download_file(self, remote_filename: str, local_path: str) -> bool:
        return self.provider.download_file(remote_filename, local_path)

    def delete_file(self, remote_filename: str) -> bool:
        return self.provider.delete_file(remote_filename)

    def list_files(self) -> List[str]:
        return self.provider.list_files()


storage_service = StorageService()
