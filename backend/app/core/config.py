import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# Load a project-local environment file without overriding explicitly supplied process configuration.
env_file=ROOT/'.env'
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key,value=line.split('=',1)
            if value.strip(): os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
DATA = Path(os.getenv('DATA_DIR', str(ROOT / 'data')))
DATA.mkdir(parents=True, exist_ok=True)
secret_file = DATA / '.secret'
if not os.getenv('JWT_SECRET') and not secret_file.exists():
    secret_file.write_text(secrets.token_urlsafe(64))
SECRET = os.getenv('JWT_SECRET') or secret_file.read_text().strip()
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DATA / "polaris.db"}')
if DATABASE_URL.startswith(('postgres://', 'postgresql://')):
    DATABASE_URL = 'postgresql+psycopg://' + DATABASE_URL.split('://', 1)[1]
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'
MAX_FILE = 20 * 1024 * 1024
