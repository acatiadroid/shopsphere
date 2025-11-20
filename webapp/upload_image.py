"""
Azure Blob Storage Image Upload Script for ShopSphere

This script uploads images to Azure Blob Storage CDN for use in product listings.

Requirements:
    pip install azure-storage-blob python-dotenv

Usage:
    python upload_image.py <image_file>
    python upload_image.py product.jpg
    python upload_image.py C:/Users/Luke/Pictures/laptop.png

Environment Variables (.env):
    AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
"""

import os
import sys
from pathlib import Path

try:
    from azure.storage.blob import BlobServiceClient, ContentSettings
    from dotenv import load_dotenv
except ImportError:
    print("❌ Required packages not installed!")
    print("\nPlease install:")
    print("  pip install azure-storage-blob python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configuration
STORAGE_ACCOUNT = "shopsphere"
CONTAINER_NAME = "cdn"
CDN_BASE_URL = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{CONTAINER_NAME}"

# Get connection string from environment
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

# Alternative: Use account key
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

# Supported image formats
SUPPORTED_FORMATS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def get_content_type(filename):
    """Get content type based on file extension"""
    ext = Path(filename).suffix.lower()
    return SUPPORTED_FORMATS.get(ext, "application/octet-stream")


def upload_image(file_path, custom_name=None):
    """
    Upload image to Azure Blob Storage

    Args:
        file_path (str): Path to the image file
        custom_name (str, optional): Custom name for the blob. Defaults to original filename.

    Returns:
        str: URL of the uploaded image
    """
    # Validate file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get file info
    file_path = Path(file_path)
    file_ext = file_path.suffix.lower()

    # Validate file format
    if file_ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format: {file_ext}\n"
            f"Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}"
        )

    # Determine blob name
    blob_name = custom_name if custom_name else file_path.name

    # Ensure blob name has extension
    if not Path(blob_name).suffix:
        blob_name += file_ext

    print(f"📤 Uploading: {file_path.name}")
    print(f"📝 Blob name: {blob_name}")
    print(f"📦 Container: {CONTAINER_NAME}")

    try:
        # Create BlobServiceClient
        if CONNECTION_STRING:
            blob_service_client = BlobServiceClient.from_connection_string(
                CONNECTION_STRING
            )
        elif ACCOUNT_KEY:
            blob_service_client = BlobServiceClient(
                account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
                credential=ACCOUNT_KEY,
            )
        else:
            raise ValueError(
                "❌ Azure credentials not found!\n\n"
                "Please set one of the following in your .env file:\n"
                "  AZURE_STORAGE_CONNECTION_STRING=...\n"
                "  AZURE_STORAGE_ACCOUNT_KEY=..."
            )

        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=blob_name
        )

        # Get content type
        content_type = get_content_type(blob_name)

        # Upload file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )

        # Generate URL
        image_url = f"{CDN_BASE_URL}/{blob_name}"

        print(f"✅ Upload successful!")
        print(f"\n📸 Image URL:")
        print(f"   {image_url}")
        print(f"\n💡 Use this URL in the admin product form")

        return image_url

    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        raise


def upload_multiple(file_paths):
    """Upload multiple images"""
    results = []
    failed = []

    print(f"\n📤 Uploading {len(file_paths)} images...\n")

    for i, file_path in enumerate(file_paths, 1):
        try:
            print(f"[{i}/{len(file_paths)}] ", end="")
            url = upload_image(file_path)
            results.append((file_path, url))
            print()
        except Exception as e:
            print(f"❌ Failed: {str(e)}\n")
            failed.append((file_path, str(e)))

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Successful: {len(results)}")
    print(f"❌ Failed: {len(failed)}")
    print("=" * 60)

    if results:
        print("\n📸 Uploaded Images:")
        for file_path, url in results:
            print(f"  • {Path(file_path).name}")
            print(f"    {url}")

    if failed:
        print("\n❌ Failed Uploads:")
        for file_path, error in failed:
            print(f"  • {Path(file_path).name}: {error}")

    return results, failed


def list_images():
    """List all images in the CDN container"""
    try:
        if CONNECTION_STRING:
            blob_service_client = BlobServiceClient.from_connection_string(
                CONNECTION_STRING
            )
        elif ACCOUNT_KEY:
            blob_service_client = BlobServiceClient(
                account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
                credential=ACCOUNT_KEY,
            )
        else:
            raise ValueError("Azure credentials not found!")

        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blobs = container_client.list_blobs()

        images = []
        for blob in blobs:
            if any(blob.name.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
                images.append(blob)

        if images:
            print(f"\n📸 Images in CDN ({len(images)} total):\n")
            for blob in images:
                size_mb = blob.size / (1024 * 1024)
                print(f"  • {blob.name}")
                print(f"    Size: {size_mb:.2f} MB")
                print(f"    URL: {CDN_BASE_URL}/{blob.name}")
                print()
        else:
            print("\n📭 No images found in CDN")

        return images

    except Exception as e:
        print(f"❌ Error listing images: {str(e)}")
        return []


def setup_env_file():
    """Create .env file template"""
    env_template = """# Azure Storage Configuration for ShopSphere
# Get your connection string from Azure Portal:
# 1. Go to Storage Account → Access Keys
# 2. Copy "Connection string"

AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here

# Alternative: Use account name and key
# AZURE_STORAGE_ACCOUNT_KEY=your_account_key_here
"""

    env_path = Path(".env")
    if env_path.exists():
        print("⚠️  .env file already exists")
        response = input("Overwrite? (y/N): ")
        if response.lower() != "y":
            print("Cancelled")
            return

    with open(env_path, "w") as f:
        f.write(env_template)

    print("✅ Created .env file")
    print("\n📝 Next steps:")
    print("  1. Edit .env file")
    print("  2. Add your Azure Storage connection string")
    print("  3. Run: python upload_image.py <image_file>")


def main():
    """Main function"""
    print("=" * 60)
    print("  ShopSphere Image Upload Tool")
    print("=" * 60)

    # Check for arguments
    if len(sys.argv) < 2:
        print("\n❌ No file specified!\n")
        print("Usage:")
        print("  python upload_image.py <image_file>")
        print("  python upload_image.py product.jpg")
        print("  python upload_image.py image1.jpg image2.png image3.jpg")
        print("\nCommands:")
        print("  python upload_image.py --list        # List all images")
        print("  python upload_image.py --setup       # Create .env file")
        print("\nSupported formats:")
        print(f"  {', '.join(SUPPORTED_FORMATS.keys())}")
        sys.exit(1)

    # Handle commands
    if sys.argv[1] == "--list":
        list_images()
        sys.exit(0)

    if sys.argv[1] == "--setup":
        setup_env_file()
        sys.exit(0)

    # Check for credentials
    if not CONNECTION_STRING and not ACCOUNT_KEY:
        print("\n❌ Azure credentials not configured!\n")
        print("Please set up your .env file:")
        print("  python upload_image.py --setup")
        print("\nThen add your connection string from Azure Portal.")
        sys.exit(1)

    # Get file paths
    file_paths = sys.argv[1:]

    # Upload single or multiple files
    if len(file_paths) == 1:
        try:
            upload_image(file_paths[0])
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            sys.exit(1)
    else:
        upload_multiple(file_paths)


if __name__ == "__main__":
    main()
