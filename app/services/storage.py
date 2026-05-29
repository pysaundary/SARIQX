from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from app.core.collector import collector
from loguru import logger

# ==========================================
# 1. THE ABSTRACT INTERFACE (Rulebook)
# ==========================================
class StorageProvider(ABC):
    @abstractmethod
    async def upload_file(self, file_bytes: bytes, filename: str, tenant_id: str | None, student_id: str) -> str:
        """Uploads bytes and returns a public accessible URL/path."""
        pass

# ==========================================
# 2. LOCAL STORAGE IMPLEMENTATION
# ==========================================
class LocalStorageProvider(StorageProvider):
    def __init__(self):
        self.base_dir = Path(collector.get("MEDIA_ROOT_DIR", "media"))
        # Ensure base media directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file_bytes: bytes, filename: str, tenant_id: str | None, student_id: str) -> str:
        # 1. Path Generation Logic: tenant / student / date /
        safe_tenant = str(tenant_id) if tenant_id else "global_pool"
        safe_student = str(student_id)
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        target_dir = self.base_dir / safe_tenant / safe_student / date_str
        target_dir.mkdir(parents=True, exist_ok=True) # Create nested folders if not exist
        
        # 2. Collision Logic (Agar same naam ki file hui toh _1, _2 lagayega)
        safe_filename = filename or "uploaded_file.bin"
        stem = Path(safe_filename).stem
        suffix = Path(safe_filename).suffix
        
        final_path = target_dir / safe_filename
        counter = 1
        
        while final_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            final_path = target_dir / new_name
            counter += 1
            
        # 3. Save the optimized bytes synchronously (safe for local disk IO)
        with final_path.open("wb") as buffer:
            buffer.write(file_bytes)
            
        logger.info(f"💾 Optimized File Saved Locally: {final_path}")
        
        # 4. Return the accessible URL path
        # Assuming we will mount the 'media' folder in FastAPI later
        return f"/{final_path.as_posix().lstrip('/')}"

# ==========================================
# 3. S3 STORAGE IMPLEMENTATION (For Future)
# ==========================================
class S3StorageProvider(StorageProvider):
    async def upload_file(self, file_bytes: bytes, filename: str, tenant_id: str | None, student_id: str) -> str:
        # Pura S3 ka logic yahan aayega baad me (boto3 use karke)
        # Ye bas dikhane ke liye hai ki switch kitna aasan hoga!
        logger.info(f"Uploading {filename} ({len(file_bytes)} bytes) to AWS S3...")
        return f"https://s3.amazonaws.com/sariqx-bucket/{tenant_id}/{student_id}/{filename}"
