# Label Studio Cloud Storage Configuration

## Quick Reference: Configure Shared Storage in Label Studio

### Step 1: Open Label Studio Settings

1. Go to http://localhost:8080
2. Click on your project name
3. Click the **Settings** tab (⚙️ gear icon)

### Step 2: Navigate to Cloud Storage

1. In the left sidebar, click **Cloud Storage**
2. Click the **Add Source Storage** button

### Step 3: Select Local Files

1. In the storage type dropdown, select **Local Files**
2. You'll see a configuration form

### Step 4: Configure Settings

Fill in the form with these **exact values**:

```
┌─────────────────────────────────────────────────────────┐
│ Add Local Files Storage                                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Title *                                                 │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Shared Storage                                     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Absolute local path *                                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │ /shared-data/upload                                │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  File Filter Regex (optional)                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │ .*\.(jpg|jpeg|png|gif|bmp)$                        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ☑ Treat every bucket object as a source file          │
│  ☑ Use pre-signed URLs                                  │
│  ☐ Enable CORS for pre-signed URLs                     │
│                                                          │
│           [ Cancel ]        [ Add Storage ]             │
└─────────────────────────────────────────────────────────┘
```

### Step 5: Add the Storage

1. Click **Add Storage**
2. You should see "Storage successfully added" message
3. The storage will appear in your Cloud Storage list

### Step 6: Sync Storage (Optional)

If you already have files in `shared-data/upload/`:

1. Click the **Sync** button next to your storage
2. Wait for sync to complete
3. Files will appear as tasks in your project

---

## Alternative Method: Import Files Directly

If you don't want to configure cloud storage, you can import files directly:

### Option A: Upload via UI

1. Go to your project
2. Click **Import** button
3. Select **Upload Files**
4. Choose images from your computer
5. Label Studio will store them in `/shared-data/upload/`

### Option B: Copy to Shared Directory

```powershell
# Copy your images to the shared directory
cp your-images\*.png shared-data\upload\

# Then in Label Studio, use Cloud Storage import
# or create tasks manually
```

---

## Verification

After configuration, verify it's working:

### 1. Check Storage is Listed

Go to **Settings** → **Cloud Storage**

You should see:
```
┌────────────────────────────────────────────────────┐
│ Source Storages                                    │
├────────────────────────────────────────────────────┤
│                                                     │
│  📁 Shared Storage                                 │
│     Local: /shared-data/upload                     │
│     Status: ✅ Active                              │
│     Tasks: 0                                       │
│                                                     │
│     [Sync] [Edit] [Delete]                         │
│                                                     │
└────────────────────────────────────────────────────┘
```

### 2. Upload a Test Image

1. Project → Import → Upload Files
2. Upload a test image
3. Check if it appears in `shared-data\upload\` on your computer:

```powershell
ls shared-data\upload\ -Recurse

# You should see:
# shared-data\upload\1\<your-image>.png
```

### 3. Create an Annotation

1. Click on a task
2. Draw a bounding box
3. Add a label
4. Click **Submit**

### 4. Watch Webhook Pipeline

Check webhook server logs:

```
✅ Expected output:
Step: webhook_received - Received ANNOTATION_CREATED event for project 1
Step: fetching_annotations - Fetching annotations from Label Studio...
Retrieved 1 annotations from Label Studio
Step: creating_dataset - Creating dataset version in ClearML...
Mapped Docker path /data/upload/1/image.png to local path shared-data\upload\1\image.png
Adding local image: shared-data\upload\1\image.png
✅ Image added successfully!
Dataset updated with 1 annotations from Label Studio
```

### 5. Check ClearML Dataset

1. Open https://app.clear.ml
2. Navigate to **ImageAnnotation** project
3. Click **Datasets** tab
4. Open latest dataset version
5. You should see:
   - `annotations_*.json` file
   - `images/` folder with your uploaded images ✨

---

## Troubleshooting

### "Path does not exist" Error

**Error**: `The path /shared-data/upload does not exist in container`

**Solution**: 
1. Verify volume mount:
   ```powershell
   docker exec label-studio ls /shared-data
   ```
2. If directory doesn't exist, create it:
   ```powershell
   docker exec label-studio mkdir -p /shared-data/upload
   ```
3. Or restart containers:
   ```powershell
   docker-compose down && docker-compose up -d
   ```

### "Permission denied"

**Error**: Label Studio can't write to `/shared-data/upload`

**Solution**:
```powershell
# Fix permissions on Windows
icacls shared-data /grant Everyone:F /T

# Or on the container side:
docker exec -u root label-studio chmod -R 777 /shared-data
```

### Files Not Appearing After Upload

**Check 1**: Is the upload directory correct?
```powershell
# Files should be in:
shared-data\upload\<project-id>\<file-name>

# Example:
shared-data\upload\1\image001.png
```

**Check 2**: Check Label Studio logs:
```powershell
docker logs label-studio | Select-String "shared-data"
```

### Tasks Not Importing from Cloud Storage

**Solution**: Click the **Sync** button in Cloud Storage settings

**Alternative**: Manually trigger sync:
1. Settings → Cloud Storage
2. Click three dots (...) next to storage
3. Click **Sync**

---

## Advanced Configuration

### Custom Upload Path

To change where files are stored:

1. Update `docker-compose.yml`:
   ```yaml
   environment:
     LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT: /shared-data/my-custom-path
   ```

2. Update `.env`:
   ```bash
   SHARED_DATA_DIR=./shared-data/my-custom-path
   ```

3. In Label Studio, use path: `/shared-data/my-custom-path`

### File Filtering

Use regex to filter specific file types:

```regex
# Only PNG and JPG
.*\.(png|jpg|jpeg)$

# Only specific prefix
^project_.*\.(png|jpg)$

# All image formats
.*\.(png|jpg|jpeg|gif|bmp|tiff|webp)$
```

### Multiple Storage Sources

You can add multiple cloud storage sources:

1. `Shared Storage` - Local files from `/shared-data/upload`
2. `AWS S3 Bucket` - Remote files from S3
3. `Azure Blob` - Remote files from Azure
4. `Google Cloud Storage` - Remote files from GCS

Each storage can be synced independently.

---

## Best Practices

1. **Use meaningful storage names**: "Shared Storage", "Production Images", etc.
2. **Set file filter regex**: Prevents importing non-image files
3. **Sync regularly**: Click Sync to import new files
4. **Monitor disk space**: Check `shared-data/` size periodically
5. **Backup important data**: Copy `shared-data/` to backup location

---

## What's Next?

After configuring cloud storage:

1. ✅ Upload images to Label Studio
2. ✅ Create annotations
3. ✅ Webhook automatically syncs to ClearML
4. ✅ Images included in dataset (no more failures!)
5. ✅ Use dataset for training

**Your pipeline is now complete and optimized!** 🎉

---

## Support Links

- [Label Studio Cloud Storage Docs](https://labelstud.io/guide/storage.html)
- [Label Studio Local Files Setup](https://labelstud.io/guide/storage.html#Local-storage)
- [Docker Volume Documentation](https://docs.docker.com/storage/volumes/)

---

**Need Help?** Check the main README.md or SHARED_STORAGE_SETUP.md
