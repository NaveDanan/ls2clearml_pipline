# Step-by-Step Setup Guide

This guide will walk you through setting up the complete Label Studio to ClearML pipeline.

## Prerequisites Checklist

- [ ] Python 3.11 or higher installed
- [ ] Docker Desktop installed and running
- [ ] Git installed (optional)
- [ ] ClearML account created (sign up at https://clear.ml)

## Step 1: Install Python Dependencies

Open PowerShell in your project directory and run:

```powershell
# Install the project and dependencies
pip install -e .
```

Expected output:
```
Successfully installed ls2clearml-pipline-0.1.0 clearml-2.0.2 fastapi-0.120.0 ...
```

## Step 2: Create Configuration File

```powershell
# Copy the example environment file
Copy-Item .env.example .env
```

Open `.env` in your text editor and fill in the configuration. For now, leave the API keys blank - we'll fill them in later.

## Step 3: Start Label Studio and PostgreSQL

```powershell
# Start Docker services
docker-compose up -d
```

Expected output:
```
Creating network "ls2clearml_pipline_ls_network" ... done
Creating labelstudio-postgres ... done
Creating label-studio ... done
```

Wait 30 seconds for services to initialize, then check status:

```powershell
docker-compose ps
```

You should see both services running (State: Up).

## Step 4: Configure Label Studio

1. **Open Label Studio**: Navigate to http://localhost:8080 in your browser

2. **Create Account**:
   - Click "Sign Up"
   - Enter email and password
   - Complete registration

3. **Generate API Token**:
   - Click on your username (top right)
   - Go to "Account & Settings"
   - Click "Access Token" tab
   - Copy your token

4. **Add Token to .env**:
   ```powershell
   notepad .env
   ```
   Set: `LABEL_STUDIO_API_KEY=<your-token-here>`

## Step 5: Configure ClearML

### Get ClearML Credentials

1. Go to https://app.clear.ml
2. Sign in or create a free account
3. Click your profile icon → "Settings"
4. Go to "Workspace" → "App Credentials"
5. Click "Create new credentials"
6. Copy the credentials shown

### Initialize ClearML

Run the initialization command:

```powershell
clearml-init
```

When prompted:
1. Paste your ClearML API credentials
2. Confirm the configuration

The configuration will be saved to `~/clearml.conf`.

### Update .env File

```powershell
notepad .env
```

Add your ClearML credentials:
```
CLEARML_API_ACCESS_KEY=<your-access-key>
CLEARML_API_SECRET_KEY=<your-secret-key>
```

## Step 6: Run Pipeline Setup

```powershell
python setup_pipeline.py
```

Expected output:
```
============================================================
Label Studio to ClearML Pipeline Setup
============================================================
INFO - Verifying environment configuration...
INFO - ✓ Environment configuration OK
INFO - Setting up ClearML configuration...
INFO - ✓ ClearML configuration successful
INFO - Setting up Label Studio project...
INFO - ✓ Created new project: ImageAnnotation (ID: 1)
INFO - Setting up webhook...
INFO - ✓ Webhook created: http://host.docker.internal:8000/webhook/label-studio
============================================================
Setup Summary
============================================================
INFO - ClearML: ✓ OK
INFO - Label Studio: ✓ OK
INFO - Webhook: ✓ OK

✓ Pipeline setup complete!

Next steps:
1. Start the webhook server: python webhook_server.py
2. Start annotating in Label Studio
3. Annotations will automatically sync to ClearML
```

## Step 7: Start Webhook Server

Open a new PowerShell window and run:

```powershell
python webhook_server.py
```

Expected output:
```
INFO - Starting webhook server on 0.0.0.0:8000
INFO - Started server process
INFO - Waiting for application startup.
INFO - Application startup complete.
INFO - Uvicorn running on http://0.0.0.0:8000
```

Keep this window open - the server needs to run continuously.

## Step 8: Test the Pipeline

### Upload Sample Images

1. Go to http://localhost:8080
2. Open your "ImageAnnotation" project
3. Click "Import"
4. Add image URLs or upload local images
5. Click "Import"

### Create Annotations

1. Click on a task to open it
2. Draw bounding boxes around objects
3. Assign labels
4. Click "Submit"

### Verify Webhook

In the webhook server terminal, you should see:
```
INFO - Received webhook: ANNOTATION_CREATED
INFO - Processing annotation update for project 1
INFO - Retrieved 1 annotations from Label Studio
INFO - Created dataset version: xxxxx
INFO - Updated ClearML dataset: xxxxx
```

### Check ClearML

1. Go to https://app.clear.ml
2. Navigate to "Datasets"
3. Find your "ImageAnnotation" project
4. You should see a new dataset version with your annotations

## Step 9: Run Training Pipeline (Optional)

```powershell
# Open a new PowerShell window
python run_pipeline.py
```

This will:
- Create a ClearML pipeline
- Execute data preparation
- Run training (with example code)
- Perform evaluation

Monitor progress at https://app.clear.ml

## Verification Checklist

- [ ] Docker services running (`docker-compose ps`)
- [ ] Label Studio accessible at http://localhost:8080
- [ ] API token configured in `.env`
- [ ] ClearML credentials configured
- [ ] Webhook server running
- [ ] Test annotation created
- [ ] Webhook received and processed
- [ ] Dataset visible in ClearML

## Common Issues

### Issue: "Connection refused" when accessing Label Studio

**Solution**: Wait 1-2 minutes after running `docker-compose up` for services to fully start.

### Issue: "Invalid API key" in webhook server

**Solution**: Verify `LABEL_STUDIO_API_KEY` in `.env` matches the token from Label Studio.

### Issue: Webhook not receiving events

**Solution**: 
1. Check webhook server is running
2. Verify webhook URL in Label Studio project settings
3. In Label Studio, go to Project Settings → Webhooks
4. URL should be: `http://host.docker.internal:8000/webhook/label-studio`

### Issue: ClearML credentials not working

**Solution**: 
1. Delete `~/clearml.conf`
2. Run `clearml-init` again
3. Get fresh credentials from https://app.clear.ml/settings/workspace-configuration

### Issue: Docker services won't start

**Solution**:
```powershell
# Stop all services
docker-compose down

# Remove volumes and restart
docker-compose down -v
docker-compose up -d
```

## Next Steps

Now that your pipeline is set up:

1. **Customize Labels**: Edit label configuration in `label_studio_client.py`
2. **Add Training Logic**: Implement your model in `example_training.py`
3. **Customize Pipeline**: Modify pipeline steps in `clearml_manager.py`
4. **Scale Up**: Add more annotation tasks and train your models

## Support

If you encounter issues:

1. Check the troubleshooting section in `README.md`
2. Review logs: `docker-compose logs -f`
3. Check webhook server output for errors
4. Verify all credentials in `.env` file

Happy annotating and training! 🚀
