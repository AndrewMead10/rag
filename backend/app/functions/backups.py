import os
import shutil
import asyncio
from datetime import datetime, timedelta
from ..database.models import PasswordResetToken
from ..database import get_db_session
from ..config import settings


def local_backup(db_path: str = "./data/service.db", backups_dir: str = "./data/backups") -> str:
    """Create a local backup of the SQLite database"""
    os.makedirs(backups_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(backups_dir, f"service-{ts}.db")
    shutil.copy2(db_path, dest)
    return dest


def upload_to_r2(filepath: str):
    """Upload backup to Cloudflare R2"""
    if not settings.enable_r2_backup:
        return
        
    try:
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
        )
        
        key = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            s3.upload_fileobj(f, settings.r2_bucket, key)
    except Exception as e:
        print(f"R2 backup failed: {e}")


async def daily_backup_loop():
    """Run daily backups"""
    while True:
        try:
            backup_path = local_backup()
            print(f"Created backup: {backup_path}")
            upload_to_r2(backup_path)
        except Exception as e:
            print(f"Backup failed: {e}")
        
        await asyncio.sleep(60 * 60 * 24)  # 24 hours


async def cleanup_expired_tokens():
    """Clean up expired password reset tokens"""
    while True:
        try:
            with get_db_session() as db:
                expired = db.query(PasswordResetToken).filter(
                    PasswordResetToken.expires_at < datetime.utcnow(),
                    PasswordResetToken.active == True
                )
                count = expired.update({"active": False})
                db.commit()
                if count > 0:
                    print(f"Cleaned up {count} expired tokens")
        except Exception as e:
            print(f"Token cleanup failed: {e}")
        
        await asyncio.sleep(3600)  # 1 hour