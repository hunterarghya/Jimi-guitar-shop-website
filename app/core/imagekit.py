from imagekitio import ImageKit
from app.core.config import get_settings
import base64
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

imagekit = ImageKit(
    private_key=settings.IMAGEKIT_PRIVATE_KEY,
    public_key=settings.IMAGEKIT_PUBLIC_KEY,
    url_endpoint=settings.IMAGEKIT_URL_ENDPOINT
)

class ImageKitUploadOptions:
    """ImageKit upload options as an object, as required by the SDK."""
    def __init__(self, folder=None, use_unique_file_name=True):
        self.folder = folder
        self.use_unique_file_name = use_unique_file_name

class ImageKitHelper:
    """Helper class for ImageKit operations."""
    
    @staticmethod
    async def upload_file(file_content: bytes, file_name: str, folder: str = "general") -> dict:
        """
        Upload a file to ImageKit.
        """
        try:
            # Convert bytes to base64
            file_b64 = base64.b64encode(file_content).decode("utf-8")
            
            # The SDK expects options to be an object with attributes, not a dict
            options = ImageKitUploadOptions(
                folder=f"jimi/{folder}",
                use_unique_file_name=True
            )
            
            upload = imagekit.upload_file(
                file=file_b64,
                file_name=file_name,
                options=options
            )
            
            # Defensive check: handle both object and dict responses
            if isinstance(upload, dict):
                return {
                    "url": upload.get("url"),
                    "file_id": upload.get("fileId"),
                    "name": upload.get("name"),
                    "thumbnail_url": upload.get("thumbnailUrl", upload.get("url"))
                }
            
            return {
                "url": getattr(upload, "url", None),
                "file_id": getattr(upload, "file_id", None) or getattr(upload, "fileId", None),
                "name": getattr(upload, "name", None),
                "thumbnail_url": getattr(upload, "thumbnail_url", getattr(upload, "url", None))
            }
        except Exception as e:
            logger.error(f"ImageKit SDK error: {str(e)}")
            raise Exception(f"ImageKit upload failed: {str(e)}")

    @staticmethod
    def delete_file(file_id: str) -> bool:
        """Delete a file from ImageKit."""
        try:
            imagekit.delete_file(file_id)
            return True
        except Exception:
            return False