# Troubleshooting 403 Forbidden Error

If you're seeing a 403 error when trying to view videos, here are the most common causes and solutions:

## Common Causes

### 1. S3 Bucket Permissions Issue

**Symptom**: 403 error when trying to access videos from S3

**Solution**:
- Check IAM user permissions - ensure the user has `s3:GetObject` and `s3:ListBucket` permissions
- Verify bucket policy allows access
- Check if bucket is public (if using public URLs)

**Test**: Visit `/api/debug/s3` endpoint to check S3 connectivity

### 2. S3 CORS Configuration

**Symptom**: Videos don't load in browser, 403 in browser console

**Solution**: Add CORS configuration to your S3 bucket:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

### 3. Presigned URL Generation Failure

**Symptom**: Videos not loading, errors in server logs

**Solution**:
- Check AWS credentials are correct
- Verify IAM user has `s3:GetObject` permission
- Check if bucket name and region are correct

### 4. Bucket Not Found or Wrong Region

**Symptom**: No videos loading, errors in logs

**Solution**:
- Verify bucket name in `S3_BUCKET_NAME` environment variable
- Check region matches bucket region
- Ensure bucket exists

## Diagnostic Steps

### Step 1: Check S3 Configuration

Visit: `http://your-server:5001/api/debug/s3`

This will show:
- S3 configuration status
- Bucket access status
- Credentials status
- Any error messages

### Step 2: Check Server Logs

```bash
# If running in Docker
docker logs reels_app

# If running locally
# Check terminal output where Flask is running
```

Look for:
- S3 connection errors
- Access denied errors
- Bucket not found errors

### Step 3: Test S3 Access Manually

```python
import boto3
import os

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('S3_REGION', 'us-east-1')
)

# Test bucket access
try:
    s3.head_bucket(Bucket='your-bucket-name')
    print("Bucket access OK")
except Exception as e:
    print(f"Error: {e}")

# List objects
try:
    response = s3.list_objects_v2(Bucket='your-bucket-name', Prefix='reels/')
    print(f"Found {response.get('KeyCount', 0)} objects")
except Exception as e:
    print(f"Error: {e}")
```

### Step 4: Check Browser Console

Open browser developer tools (F12) and check:
- Network tab for failed requests
- Console for CORS errors
- Check if video URLs are being generated

## Quick Fixes

### Fix 1: Use Local Files (Temporary)

If S3 is causing issues, temporarily disable S3:

1. Remove or comment out S3 environment variables in `.env`:
```bash
# S3_BUCKET_NAME=your-bucket-name
```

2. Restart Flask application
3. Application will automatically use local `static/reels/` folder

### Fix 2: Make S3 Bucket Public (Not Recommended for Production)

1. Go to S3 Console → Your Bucket → Permissions
2. Unblock public access
3. Add bucket policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

4. Set `S3_USE_PRESIGNED_URLS=false` in `.env`

### Fix 3: Fix IAM Permissions

Ensure your IAM user has this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

## Verify Fix

After applying fixes:

1. Restart Flask application
2. Visit `/api/debug/s3` to verify S3 connectivity
3. Visit `/api/reels` to check if videos are listed
4. Try loading a video URL directly in browser
5. Check browser console for any remaining errors

## Still Having Issues?

1. Check application logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test S3 access using AWS CLI:
   ```bash
   aws s3 ls s3://your-bucket-name/reels/
   ```
4. Check if videos exist in the S3 bucket folder
5. Verify video file names match expected format

