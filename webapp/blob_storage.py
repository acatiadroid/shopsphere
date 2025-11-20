"""
Azure Blob Storage utility for ShopSphere image uploads

This module handles uploading product images to Azure Blob Storage CDN.
"""

import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient, ContentSettings
from werkzeug.utils import secure_filename

# Configuration
STORAGE_ACCOUNT = "shopsphere"
CONTAINER_NAME = "cdn"
CDN_BASE_URL = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{CONTAINER_NAME}"

# Get connection string from environment
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

# Supported image formats
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

# Max file size (5MB)
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
            "Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_KEY in environment."
        )


def allowed_file(filename):
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def get_content_type(filename):
    """Get content type based on file extension"""
    ext = Path(filename).suffix.lower()
    return CONTENT_TYPES.get(ext, "application/octet-stream")


def upload_image(file_storage, custom_name=None):
    """
    Upload image to Azure Blob Storage CDN

    Args:
        file_storage: FileStorage object from Flask request.files
        custom_name: Optional custom name for the blob (without extension)

    Returns:
        str: URL of the uploaded image

    Raises:
        ValueError: If file is invalid or too large
        Exception: If upload fails
    """
    # Validate file
    if not file_storage:
        raise ValueError("No file provided")

    if file_storage.filename == "":
        raise ValueError("No file selected")

    if not allowed_file(file_storage.filename):
        raise ValueError(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Check file size
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large. Max size: {MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
        )

    if file_size == 0:
        raise ValueError("File is empty")

    # Generate blob name
    original_filename = secure_filename(file_storage.filename)
    file_ext = Path(original_filename).suffix.lower()

    if custom_name:
        blob_name = secure_filename(custom_name)
        if not blob_name.endswith(file_ext):
            blob_name += file_ext
    else:
        blob_name = original_filename

    # Get blob client
    blob_service_client = get_blob_service_client()
    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME, blob=blob_name
    )

    # Get content type
    content_type = get_content_type(blob_name)

    # Upload file
    blob_client.upload_blob(
        file_storage,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )

    # Generate and return URL
    image_url = f"{CDN_BASE_URL}/{blob_name}"
    return image_url


def delete_image(blob_name):
    """
    Delete image from Azure Blob Storage

    Args:
        blob_name: Name of the blob to delete

    Returns:
        bool: True if deleted successfully
    """
    try:
        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=blob_name
        )
        blob_client.delete_blob()
        return True
    except Exception:
        return False


def list_images():
    """
    List all images in the CDN container

    Returns:
        list: List of blob names
    """
    try:
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blobs = container_client.list_blobs()
        return [
            blob.name
            for blob in blobs
            if Path(blob.name).suffix.lower() in ALLOWED_EXTENSIONS
        ]
    except Exception:
        return []
