from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from loguru import logger

from app.api.deps import get_current_user, get_storage_provider
from app.models.auth import User
from app.services.storage import StorageProvider
from app.core.collector import collector
from app.utils.image import optimize_image # ⚡ Import the optimizer!

router = APIRouter(prefix="/attachments", tags=["SARIQX Media Processing"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    storage: StorageProvider = Depends(get_storage_provider)
):
    # 1. Security Check: Ensure it's actually an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed for optimization.")
        
    # 2. Read the raw massive file into memory
    raw_bytes = await file.read()
    
    # 3. ⚡ PASS THROUGH THE OPTIMIZATION ENGINE
    try:
        opt_bytes, opt_filename, opt_content_type = optimize_image(raw_bytes, file.filename)
        logger.info(f"🗜️ Image Compressed! Original: {len(raw_bytes)/1024:.0f}KB -> New: {len(opt_bytes)/1024:.0f}KB")
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise HTTPException(status_code=422, detail="Unable to process the image file.")
    
    # 4. Save the tiny WEBP file via provider
    relative_path = await storage.upload_file(
        file_bytes=opt_bytes,
        filename=opt_filename,
        tenant_id=current_user.tenant_id,
        student_id=str(current_user.id)
    )
    
    # 5. Resolve absolute URL dynamically
    base_url = collector.get("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
    absolute_url = f"{base_url}{relative_path}" if not relative_path.startswith("http") else relative_path
    
    return {
        "filename": opt_filename,
        "content_type": opt_content_type,
        "relative_path": relative_path,
        "full_url": absolute_url 
    }