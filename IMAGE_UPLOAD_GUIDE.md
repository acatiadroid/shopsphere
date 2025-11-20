# Image Upload Guide for ShopSphere

This guide explains how product images are uploaded to Azure Blob Storage CDN when adding products to the store.

## Overview

ShopSphere uses a **serverless architecture** where the **product-catalog Azure Function** handles uploading images to Azure Blob Storage CDN. The webapp sends base64-encoded image data to the Azure Function, which then uploads it to the CDN and returns the image URL.

## Architecture

```
┌─────────────────┐
│   Flask WebApp  │  (No direct Azure Storage access)
└────────┬────────┘
         │
         │ Base64 Image Data
         ▼
┌────────────────────┐
│  Product-Catalog   │  (Has Azure Storage credentials)
│  (Azure Function)  │
└────────┬───────────┘
         │
         │ Upload Image
         ▼
┌────────────────────┐
│  Azure Blob Storage│
│   (CDN Container)  │
└────────────────────┘
```

**Key Points:**
- ✅ Webapp collects image file from user
- ✅ Webapp converts image to base64
- ✅ Webapp sends base64 data to product-catalog Azure Function
- ✅ Azure Function uploads to blob storage
- ✅ Azure Function returns CDN URL
- ✅ Product is created with image URL

## Setup

### 1. Configure Azure Storage Credentials (Azure Function Only)

**Important:** Azure Storage credentials are configured in the **product-catalog Azure Function**, NOT the webapp.

#### For Local Development (Azure Function)

1. Navigate to the product-catalog directory:
```bash
cd product-catalog
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Edit `.env` and add your Azure Storage connection string:
```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=shopsphere;AccountKey=YOUR_KEY_HERE;EndpointSuffix=core.windows.net
```

#### For Azure Deployment (Azure Function)

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure Function App: `product-catalog-ffcjf2heceech3f6`
3. Go to **Configuration** → **Application settings**
4. Add new application setting:
   - Name: `AZURE_STORAGE_CONNECTION_STRING`
   - Value: Your connection string from Storage Account

#### Getting Azure Storage Credentials

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to Storage Account: `shopsphere`
3. Go to **Security + networking** → **Access keys**
4. Copy **Connection string** from Key1 or Key2
5. Paste it into the Azure Function's configuration

### 2. Install Dependencies

#### Webapp (No Azure Storage dependency needed)
```bash
cd webapp
pip install -r requirements.txt
```

Dependencies:
- Flask
- requests
- python-dotenv

#### Product-Catalog Azure Function
```bash
cd product-catalog
pip install -r requirements.txt
```

Dependencies:
- azure-functions
- pyodbc
- azure-storage-blob  ← Handles image uploads

### 3. Verify Container Exists

Ensure the `cdn` container exists in your Azure Storage account:

1. Go to Azure Portal → Storage Account: `shopsphere`
2. Navigate to **Data storage** → **Containers**
3. Verify `cdn` container exists
4. Set public access level: **Blob (anonymous read access for blobs only)**

## Using the Image Upload Feature

### Admin Web Interface

1. **Access Admin Panel**
   - Log in with admin account (`admin@gmail.com`)
   - Navigate to `/admin/products`

2. **Add a New Product**
   - Fill in product details (name, category, price, etc.)
   - Upload an image using one of these methods:
     - **Drag and Drop**: Drag an image file onto the upload zone
     - **Click to Browse**: Click the upload zone to select a file
   
3. **Image Processing Flow**
   - Webapp reads the file
   - Webapp converts image to base64
   - Webapp sends data to product-catalog Azure Function
   - Azure Function uploads to Azure Blob Storage
   - Azure Function returns CDN URL
   - Product is created with image URL

4. **Submit the Form**
   - Click "Add Product"
   - Image is uploaded automatically
   - Product is created with the CDN URL
   - Success message shows product ID

5. **Image Specifications**
   - **Supported formats**: JPG, PNG, GIF, WebP
   - **Maximum size**: 5MB
   - **Preview**: Shows before upload
   - **Validation**: Client-side and server-side

### API Usage

#### Create Product with Image (Base64)

```http
POST /api/products
Authorization: Bearer {admin_session_token}
Content-Type: application/json

{
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": 999.99,
  "stock_quantity": 10,
  "category": "Electronics",
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA..."
}
```

**Response:**
```json
{
  "success": true,
  "product_id": 123,
  "name": "Laptop",
  "price": 999.99,
  "image_url": "https://shopsphere.blob.core.windows.net/cdn/laptop.jpg"
}
```

#### Create Product with Existing Image URL

```http
POST /api/products
Authorization: Bearer {admin_session_token}
Content-Type: application/json

{
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": 999.99,
  "stock_quantity": 10,
  "category": "Electronics",
  "image_url": "https://shopsphere.blob.core.windows.net/cdn/existing-image.jpg"
}
```

## Image URL Format

All uploaded images are stored with this URL pattern:
```
https://shopsphere.blob.core.windows.net/cdn/<filename>
```

**Examples:**
- `https://shopsphere.blob.core.windows.net/cdn/laptop.jpg`
- `https://shopsphere.blob.core.windows.net/cdn/product_a1b2c3d4e5f6.png`
- `https://shopsphere.blob.core.windows.net/cdn/shirt-blue.webp`

## Best Practices

### Image Preparation

1. **Size**: Keep images under 5MB for fast uploads
2. **Dimensions**: Recommended 800x800px or similar square ratio
3. **Format**: Use JPG for photos, PNG for graphics with transparency
4. **Optimization**: Compress images before uploading to reduce file size
5. **Naming**: Descriptive product names will be used for filenames

### File Naming

The Azure Function automatically generates safe filenames:
- Uses product name when available
- Sanitizes special characters
- Adds unique identifier if needed
- Preserves file extension based on content type

### Upload Tips

- **Check preview**: Always check the preview before submitting
- **Compression**: Pre-compress large images using tools like TinyPNG
- **Format selection**: Use WebP for best compression (when supported)
- **Test upload**: Try a small test image first
- **Timeout**: Large images may take longer to upload (30s timeout)

## Troubleshooting

### Error: "Image upload failed"

**Possible causes:**
1. Azure Storage credentials not configured in Azure Function
2. Network timeout
3. Storage container doesn't exist
4. Invalid image format

**Solutions:**
- Verify Azure Function has `AZURE_STORAGE_CONNECTION_STRING` configured
- Check Azure Portal → Function App → Configuration
- Ensure `cdn` container exists in storage account
- Reduce image size if timeout occurs

### Error: "Invalid image type"

**Solution:** Only these image formats are supported:
- JPG/JPEG
- PNG
- GIF
- WebP

### Error: "File too large"

**Solution:** 
- Maximum file size is 5MB
- Compress image using:
  - [TinyPNG](https://tinypng.com/)
  - [Compressor.io](https://compressor.io/)
  - Photoshop/GIMP "Save for Web"

### Error: "Azure Storage credentials not configured"

**Solution:**
- This error comes from the Azure Function, not the webapp
- Add `AZURE_STORAGE_CONNECTION_STRING` to the product-catalog Azure Function
- **For local development**: Add to `product-catalog/.env`
- **For Azure deployment**: Add to Function App → Configuration → Application settings

### Images Not Loading on Website

**Possible causes:**
1. CORS settings on Azure Storage
2. Container access level not set to public
3. Firewall blocking blob storage domain

**Solutions:**
1. **Configure CORS:**
   - Azure Portal → Storage Account → Resource sharing (CORS)
   - Add allowed origins: `*` (for testing) or your domain
   - Add allowed methods: `GET`

2. **Set Public Access:**
   - Azure Portal → Storage Account → Containers → `cdn`
   - Set "Public access level" to "Blob (anonymous read access for blobs only)"

3. **Check Firewall:**
   - Ensure `shopsphere.blob.core.windows.net` is accessible
   - Test URL directly in browser

## How It Works (Technical Details)

### Upload Flow

```
1. User selects image file in admin form
   ↓
2. JavaScript reads file as base64 (preview)
   ↓
3. User submits form
   ↓
4. Flask receives multipart/form-data
   ↓
5. Flask reads file and encodes to base64
   ↓
6. Flask sends JSON with base64 data to Azure Function
   {
     "name": "Product",
     "price": 29.99,
     "image_data": "data:image/jpeg;base64,..."
   }
   ↓
7. Azure Function receives request
   ↓
8. Azure Function validates base64 data
   ↓
9. Azure Function decodes base64 to bytes
   ↓
10. Azure Function uploads to Blob Storage
   ↓
11. Azure Function gets CDN URL
   ↓
12. Azure Function saves product with image_url
   ↓
13. Azure Function returns success with image_url
   ↓
14. Webapp shows success message
```

### Code Example (Webapp)

```python
# webapp/app.py (simplified)

# Read uploaded file
file = request.files['product_image']
file_bytes = file.read()

# Convert to base64
image_data = base64.b64encode(file_bytes).decode('utf-8')

# Add data URL prefix
content_type = file.content_type or 'image/jpeg'
image_data = f"data:{content_type};base64,{image_data}"

# Send to Azure Function
response = requests.post(
    f"{PRODUCT_CATALOG_URL}/products",
    json={
        "name": "Product Name",
        "price": 29.99,
        "image_data": image_data  # Base64 string
    },
    headers=get_auth_headers()
)
```

### Code Example (Azure Function)

```python
# product-catalog/CreateProduct/__init__.py (simplified)

from shared.blob_utils import upload_image_base64

# Get image data from request
image_data = req_body.get('image_data')

# Upload to blob storage
if image_data:
    image_url = upload_image_base64(image_data, filename=product_name)
    # Returns: "https://shopsphere.blob.core.windows.net/cdn/product.jpg"

# Save product with image_url
cursor.execute(
    "INSERT INTO products (..., image_url) VALUES (..., ?)",
    (..., image_url)
)
```

## Security Considerations

### Webapp Security
- ✅ Admin-only access to product creation
- ✅ Session token verification
- ✅ File type validation (client-side)
- ✅ File size validation (client-side)
- ❌ No direct Azure Storage access
- ❌ No storage credentials stored

### Azure Function Security
- ✅ Admin verification via session token
- ✅ File type validation (server-side)
- ✅ File size validation (5MB max)
- ✅ Base64 decoding validation
- ✅ Secure filename sanitization
- ✅ Storage credentials in environment variables
- ✅ No credentials exposed in responses

### Azure Storage Security
- ✅ Connection string stored securely (not in code)
- ✅ Public blob access for CDN (read-only)
- ✅ Container isolated from other data
- ✅ HTTPS-only access
- ✅ Access keys rotatable in Azure Portal

## Cost Considerations

### Azure Blob Storage Pricing

- **Storage**: ~$0.018/GB/month (Hot tier)
- **Write operations**: ~$0.05 per 10,000 transactions
- **Read operations**: ~$0.004 per 10,000 transactions
- **Bandwidth**: First 100GB free, then ~$0.087/GB

### Estimated Costs (Example)

- 1,000 products with 500KB images = 500MB storage = **~$0.01/month**
- 10,000 image uploads = **~$0.05**
- 100,000 image views = **~$0.04**
- **Total**: **<$1/month** for small stores

### Cost Optimization

- Compress images before upload (reduce storage and bandwidth)
- Use WebP format for better compression
- Set lifecycle policies to archive old/unused images
- Monitor usage in Azure Portal → Storage Account → Metrics

## Deployment Checklist

### Product-Catalog Azure Function
- [ ] Add `AZURE_STORAGE_CONNECTION_STRING` to Application Settings
- [ ] Deploy updated code with `blob_utils.py`
- [ ] Verify `azure-storage-blob` is in requirements.txt
- [ ] Test image upload via API

### Webapp
- [ ] Remove any Azure Storage credentials (not needed)
- [ ] Deploy updated code with base64 encoding
- [ ] Verify file upload form works
- [ ] Test end-to-end product creation with image

### Azure Storage
- [ ] Verify `cdn` container exists
- [ ] Set public access level to "Blob"
- [ ] Configure CORS for your webapp domain
- [ ] Test direct image access via URL

## Support

### Common Questions

**Q: Do I need Azure Storage credentials in the webapp?**
A: No! Only the product-catalog Azure Function needs storage credentials.

**Q: What format should I send images to the API?**
A: Send base64-encoded data with data URL prefix: `data:image/jpeg;base64,...`

**Q: Can I use existing image URLs?**
A: Yes! You can pass `image_url` instead of `image_data` in the API request.

**Q: What happens if the image upload fails?**
A: The Azure Function returns an error and the product is not created.

**Q: How do I delete uploaded images?**
A: Currently, images are not automatically deleted. Manual cleanup via Azure Portal or API is needed.

### Getting Help

1. Check Azure Function logs in Azure Portal
2. Verify environment variables are set
3. Test with a small test image first
4. Check network connectivity
5. Review this guide's troubleshooting section

---

**Architecture:** Serverless (Azure Functions)
**Storage:** Azure Blob Storage (CDN)
**Image Handling:** Base64 encoding/decoding
**Status:** ✅ Production Ready