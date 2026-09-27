import os
from abc import ABC, abstractmethod
from app.core.config import DATA
class StorageProvider(ABC):
    @abstractmethod
    def put(self,key,data): ...
    @abstractmethod
    def get(self,key): ...
class LocalStorage(StorageProvider):
    def __init__(self):
        self.root=DATA/'uploads'; self.root.mkdir(exist_ok=True)
    def path(self,key):
        if '/' in key or '\\' in key or '..' in key: raise ValueError('Invalid storage key')
        return self.root/key
    def put(self,key,data): self.path(key).write_bytes(data)
    def get(self,key): return self.path(key).read_bytes()
class S3CompatibleStorage(StorageProvider):
    def __init__(self):
        import boto3
        from botocore.config import Config
        self.bucket=os.environ['S3_BUCKET']
        self.client=boto3.client('s3',endpoint_url=os.getenv('S3_ENDPOINT'),
            region_name=os.getenv('S3_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('S3_ACCESS_KEY'),aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
            config=Config(signature_version='s3v4',s3={'addressing_style':'path'},
                request_checksum_calculation='when_required',response_checksum_validation='when_required',
                connect_timeout=10,read_timeout=60,retries={'max_attempts':3,'mode':'standard'}))
    def put(self,key,data): self.client.put_object(Bucket=self.bucket,Key=key,Body=data)
    def get(self,key):
        body=self.client.get_object(Bucket=self.bucket,Key=key)['Body']
        try: return body.read()
        finally: body.close()
def storage(): return S3CompatibleStorage() if os.getenv('STORAGE_PROVIDER')=='s3' else LocalStorage()
