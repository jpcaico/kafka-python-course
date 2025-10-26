import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("minio-client")


class MinIOClient:

    def __init__(
            self,
            endpoint_url: str = "http://localhost:9000",
            access_key: str = "minioadmin",
            secret_key: str = "minioadmin",
            region_name: str = "us-east-1"
    ):
        
        self.endpoint_url = endpoint_url,

        self.client = boto3.client(
            's3',
            endpoint_url = endpoint_url,
            aws_access_key_id = access_key,
            aws_secret_access_key = secret_key,
            region_name = region_name
        )

        logger.info(f"MinIO Client initialized at {endpoint_url}")


    def bucket_exists(self, bucket_name: str) -> bool:

        try:
            self.client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False
        
    
    def create_bucket(self, bucket_name: str) -> bool:

        try:
            if self.bucket_exists(bucket_name):
                logger.info(f"Bucket {bucket_name} already exists.")
                return True
            
            self.client.create_bucket(Bucket=bucket_name)
            logger.info(f"Create bucket {bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False
        
    
    def upload_file(
            self,
            file_path: str,
            bucket_name: str,
            object_name: Optional[str] = None
    ) -> bool:
        
        if object_name is None:
            object_name = Path(file_path).name

        try:
            self.client.upload_file(file_path, bucket_name, object_name)
            logger.info(f" Uploaded {object_name} to bucket {bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            return False
        
    
    def upload_bytes(
            self,
            data: bytes,
            bucket_name: str,
            object_name: str
    ) -> bool:
        
        try:
            self.client.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=data
            )

            logger.info(f"Uploaded {len(data)} bytes to s3://{bucket_name}/{object_name}")
            return True
        except ClientError as e:
            logger.error(f"Uploaded failed: {e}")
            return False
        
    
    def list_objects(
            self,
            bucket_name: str,
            prefix: str = ""
    ) -> list:
        
        "region=US/"
        "date=2025-10-24/"
        "year=2025/month=10/"
        "processed/" "raw/"

        try:
            response = self.client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )

            if 'Contents' not in response:
                logger.info(f"No objects were found in s3://{bucket_name}/{prefix}")
                return []
            
            objects = [obj['Key'] for obj in response['Contents']]
            logger.info(f"Found {len(objects)} objects in s3://{bucket_name}/{prefix}")
            return objects
        
        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            return []
        

    def delete_objects(
            self,
            bucket_name: str,
            object_name: str,
    ) -> bool:
        
        try:
            self.client.delete_object(Bucket=bucket_name, Key=object_name)
            logger.info(f"Deleted s3://{bucket_name}/{object_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete s3://{bucket_name}/{object_name} : {e}")
            return False
        


    def get_statistics(self) -> Dict[str, Any]:

        stats = {
            'total_buckets': 0,
            'buckets': {}
        }
        
        try:
            response = self.client.list_buckets()
            stats['total_buckets'] = len(response['Buckets'])
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                objects = self.list_objects(bucket_name)
                stats['buckets'][bucket_name] = len(objects)
                
        except ClientError as e:
            logger.error(f"Failed to get statistics: {e}")
            
        return stats