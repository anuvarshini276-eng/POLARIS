import io
import os
from pathlib import Path
import subprocess
import sys

from botocore.response import StreamingBody
from botocore.stub import Stubber
from app.services.storage import S3CompatibleStorage


def test_private_s3_roundtrip(monkeypatch):
    for key, value in {'S3_BUCKET':'polaris', 'S3_ENDPOINT':'https://example.invalid/storage/v1/s3',
        'S3_REGION':'ap-south-1', 'S3_ACCESS_KEY':'test-key', 'S3_SECRET_KEY':'test-secret'}.items():
        monkeypatch.setenv(key, value)
    provider = S3CompatibleStorage()
    assert provider.client.meta.region_name == 'ap-south-1'
    assert provider.client.meta.config.s3['addressing_style'] == 'path'
    raw = io.BytesIO(b'research evidence')
    with Stubber(provider.client) as stub:
        stub.add_response('put_object', {}, {'Bucket':'polaris','Key':'research.txt','Body':b'research evidence'})
        stub.add_response('get_object', {'Body':StreamingBody(raw, 17)}, {'Bucket':'polaris','Key':'research.txt'})
        provider.put('research.txt', b'research evidence')
        assert provider.get('research.txt') == b'research evidence'
        stub.assert_no_pending_responses()
    assert raw.closed


def test_admin_bootstrap_survives_restart(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'PYTHONPATH':str(root/'backend'), 'DATA_DIR':str(tmp_path),
        'DATABASE_URL':'sqlite:///'+(tmp_path/'hosted.db').as_posix(), 'STORAGE_PROVIDER':'local',
        'ADMIN_EMAIL':'owner@example.com', 'ADMIN_PASSWORD':'Initial-password-123', 'DEMO_MODE':'false',
        'LLM_PROVIDER':'mock', 'EMBEDDING_PROVIDER':'mock'}
    script = root/'scripts'/'seed_database.py'
    subprocess.run([sys.executable,str(script)],env=env,check=True,capture_output=True)
    env['ADMIN_PASSWORD']='Different-password-456'
    subprocess.run([sys.executable,str(script)],env=env,check=True,capture_output=True)
    verify = """
from sqlalchemy import select, func
from app.models.database import SessionLocal, User
from app.core.security import verify_password
with SessionLocal() as db:
    user=db.scalar(select(User).where(User.email=='owner@example.com'))
    assert user.role=='admin'
    assert verify_password('Initial-password-123',user.password)
    assert db.scalar(select(func.count()).select_from(User))==3
"""
    subprocess.run([sys.executable,'-c',verify],env=env,check=True,capture_output=True)
