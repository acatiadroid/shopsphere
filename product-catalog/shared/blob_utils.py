import base64
import logging
import os
import uuid

from azure.storage.blob import BlobServiceClient, ContentSettings

STORAGE_ACCOUNT = "shopspherecdn"
CONTAINER_NAME = "cdn"
CDN_BASE_URL = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{CONTAINER_NAME}"

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

MAX_FILE_SIZE = 5 * 1024 * 1024


def get_blob_service_client():
    """Get BlobServiceClient instance"""
    if CONNECTION_STRING:
        return BlobServiceClient.from_connection_string(CONNECTION_STRING)
    elif ACCOUNT_KEY:
        return BlobServiceClient(
            account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
            credential=ACCOUNT_KEY,
        )
    else:
        raise ValueError(
            "Azure Storage credentials not configured. "
            "Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_KEY."
        )


def get_extension_from_content_type(content_type):
    """Get file extension from content type"""
    type_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    return type_map.get(content_type, ".jpg")


def validate_image_data(image_data):
    """Validate base64 image data"""
    if not image_data:
        raise ValueError("No image data provided")

    if image_data.startswith("data:"):
        try:
            header, encoded = image_data.split(",", 1)
            content_type = header.split(";")[0].split(":")[1]

            if content_type not in CONTENT_TYPES.values():
                raise ValueError(
                    f"Invalid image type. Allowed: {', '.join(CONTENT_TYPES.values())}"
                )

            return encoded, content_type
        except Exception:
            raise ValueError("Invalid data URL format")
    else:
        return image_data, "image/jpeg"


def upload_image_base64(image_data, filename=None):
    """Upload base64 encoded image to Azure Blob Storage"""
    try:
        base64_data, content_type = validate_image_data(image_data)
        image_bytes = base64.b64decode(base64_data)

        if len(image_bytes) > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large. Max size: {MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
            )

        if len(image_bytes) == 0:
            raise ValueError("File is empty")

        if filename:
            safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
            blob_name = safe_filename
        else:
            blob_name = f"product_{uuid.uuid4().hex[:12]}"

        ext = get_extension_from_content_type(content_type)
        if not blob_name.endswith(tuple(ALLOWED_EXTENSIONS)):
            blob_name += ext

        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=blob_name
        )

        blob_client.upload_blob(
            image_bytes,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        image_url = f"{CDN_BASE_URL}/{blob_name}"
        logging.info(f"Image uploaded successfully: {image_url}")
        return image_url

    except ValueError as e:
        logging.error(f"Image validation error: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Image upload error: {str(e)}")
        raise Exception(f"Failed to upload image: {str(e)}")


def upload_image_binary(image_bytes, content_type="image/jpeg", filename=None):
    """Upload binary image data to Azure Blob Storage"""
    try:
        if content_type not in CONTENT_TYPES.values():
            raise ValueError(f"Invalid content type: {content_type}")

        if len(image_bytes) > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large. Max size: {MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
            )

        if len(image_bytes) == 0:
            raise ValueError("File is empty")

        if filename:
            safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
            blob_name = safe_filename
        else:
            blob_name = f"product_{uuid.uuid4().hex[:12]}"

        ext = get_extension_from_content_type(content_type)
        if not blob_name.endswith(tuple(ALLOWED_EXTENSIONS)):
            blob_name += ext

        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=blob_name
        )

        blob_client.upload_blob(
            image_bytes,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        image_url = f"{CDN_BASE_URL}/{blob_name}"
        logging.info(f"Image uploaded successfully: {image_url}")
        return image_url

    except ValueError as e:
        logging.error(f"Image validation error: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Image upload error: {str(e)}")
        raise Exception(f"Failed to upload image: {str(e)}")


def delete_image(blob_name):
    """Delete image from Azure Blob Storage"""
    try:
        if blob_name.startswith("http"):
            blob_name = blob_name.split("/")[-1]

        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=blob_name
        )
        blob_client.delete_blob()
        logging.info(f"Image deleted: {blob_name}")
        return True
    except Exception as e:
        logging.error(f"Failed to delete image: {str(e)}")
        return False
