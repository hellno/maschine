import os
import boto3
import modal
from botocore.exceptions import ClientError
from modal import CloudBucketMount

class ProjectVolume:
    """Manages project files in S3 bucket using CloudBucketMount"""
    BASE_MOUNT = "/s3-projects"
    BUCKET_NAME = "frameception-projects-prod"  # Hardcoded bucket name
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.bucket_name = self.BUCKET_NAME
        
        # S3 paths structure
        self.paths = {
            "repo": os.path.join(self.BASE_MOUNT, "repo", project_id),
            "tmp": os.path.join(self.BASE_MOUNT, "tmp", project_id),
            "build": os.path.join(self.BASE_MOUNT, "build", project_id)
        }
        
        # Initialize S3 client for direct operations
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )

    @classmethod
    def mount(cls) -> CloudBucketMount:
        """Create configured CloudBucketMount for Modal functions"""
        return CloudBucketMount(
            bucket_name=cls.BUCKET_NAME,
            secret=modal.Secret.from_name("aws-secret"),
            read_only=False,
            key_prefix="projects/",  # Base prefix for all projects
            # For non-AWS S3-compatible storage:
            # bucket_endpoint_url="https://your-custom-endpoint"
        )

    def delete(self):
        """Recursively delete all project data from S3"""
        try:
            # Delete all objects in project prefixes
            for prefix in [
                f"projects/repo/{self.project_id}/",
                f"projects/tmp/{self.project_id}/",
                f"projects/build/{self.project_id}/"
            ]:
                self._delete_prefix(prefix)
        except ClientError as e:
            print(f"S3 deletion error: {str(e)}")

    def _delete_prefix(self, prefix: str):
        """Helper to delete all objects under a prefix"""
        paginator = self.s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            if 'Contents' in page:
                self.s3.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': [
                        {'Key': obj['Key']} for obj in page['Contents']
                    ]}
                )
