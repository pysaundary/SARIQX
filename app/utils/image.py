import io
from PIL import Image
from fastapi import UploadFile

def optimize_image(file_bytes: bytes, original_filename: str) -> tuple[bytes, str, str]:
    """
    Takes raw image bytes, resizes if too large, compresses it, 
    and converts to WebP format for maximum storage savings.
    Returns: (optimized_bytes, new_filename, new_content_type)
    """
    # Open image from bytes
    image = Image.open(io.BytesIO(file_bytes))
    
    # Convert RGBA to RGB (WebP handles transparency, but for notes RGB is safer/smaller)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
        
    # 1. Downscale if insanely large (e.g., > 1920px width)
    max_size = (1920, 1920)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # 2. Compress and save to WebP format in memory
    output_buffer = io.BytesIO()
    # quality=80 is the sweet spot: invisible quality loss, massive size reduction
    image.save(output_buffer, format="WEBP", quality=80, optimize=True) 
    
    optimized_bytes = output_buffer.getvalue()
    
    # Create new filename (change .jpg/.png to .webp)
    import os
    base_name = os.path.splitext(original_filename)[0]
    new_filename = f"{base_name}.webp"
    
    return optimized_bytes, new_filename, "image/webp"