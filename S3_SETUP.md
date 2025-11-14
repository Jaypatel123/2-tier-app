# S3 Configuration Guide

This guide explains how to configure the Flask Reels application to serve videos from an AWS S3 bucket.

## Prerequisites

1. AWS Account
2. S3 Bucket created
3. IAM user with S3 access permissions
4. Video files uploaded to S3 bucket

## Step 1: Create S3 Bucket

1. Go to AWS S3 Console
2. Click "Create bucket"
3. Choose a unique bucket name (e.g., `my-reels-bucket`)
4. Select your preferred region (e.g., `us-east-1`)
5. Configure bucket settings:
   - **Public Access**: Choose based on your needs:
     - **Public URLs**: Uncheck "Block all public access" if you want public URLs
     - **Presigned URLs**: Keep public access blocked if using presigned URLs (recommended)
   - **Versioning**: Optional
   - **Encryption**: Recommended (SSE-S3 or SSE-KMS)

## Step 2: Upload Video Files

1. Create a folder in your bucket (e.g., `reels/`)
2. Upload all video files to this folder
3. Supported formats: `.mp4`, `.webm`, `.mov`, `.avi`, `.mkv`

## Step 3: Configure IAM User

Create an IAM user with the following permissions:

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

Or use the AWS managed policy: `AmazonS3ReadOnlyAccess` (if bucket is public)

## Step 4: Get AWS Credentials

1. Go to IAM Console → Users
2. Select your user
3. Go to "Security credentials" tab
4. Click "Create access key"
5. Choose "Application running outside AWS"
6. Save the **Access Key ID** and **Secret Access Key**

## Step 5: Configure Environment Variables

Add the following to your `.env` file:

```bash
# S3 Configuration
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
S3_REELS_FOLDER=reels/
S3_USE_PRESIGNED_URLS=true
S3_PRESIGNED_URL_EXPIRY=3600

# AWS Credentials
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
```

### Environment Variables Explained:

- **S3_BUCKET_NAME**: Your S3 bucket name
- **S3_REGION**: AWS region where your bucket is located
- **S3_REELS_FOLDER**: Folder path in S3 bucket where videos are stored (with trailing slash)
- **S3_USE_PRESIGNED_URLS**: 
  - `true`: Generate temporary presigned URLs (more secure, recommended)
  - `false`: Use public URLs (requires public bucket)
- **S3_PRESIGNED_URL_EXPIRY**: Expiry time in seconds for presigned URLs (default: 3600 = 1 hour)
- **AWS_ACCESS_KEY_ID**: Your AWS access key
- **AWS_SECRET_ACCESS_KEY**: Your AWS secret key

## Step 6: Bucket Access Options

### Option A: Public Bucket (Simple, Less Secure)

1. Unblock public access in bucket settings
2. Set bucket policy:
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
3. Set `S3_USE_PRESIGNED_URLS=false` in `.env`

### Option B: Private Bucket with Presigned URLs (Recommended)

1. Keep bucket private (block public access)
2. Ensure IAM user has `s3:GetObject` permission
3. Set `S3_USE_PRESIGNED_URLS=true` in `.env`
4. URLs will be generated with temporary access tokens

## Step 7: Test Configuration

1. Start your Flask application
2. Check logs for S3 connection status
3. Visit `/api/reels` endpoint
4. Verify that video URLs point to S3

## Troubleshooting

### Error: "AWS credentials not found"
- Check that `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set in `.env`
- Verify credentials are correct

### Error: "Access Denied"
- Check IAM user permissions
- Verify bucket name and region are correct
- Ensure IAM user has `s3:ListBucket` and `s3:GetObject` permissions

### Error: "Bucket not found"
- Verify bucket name in `S3_BUCKET_NAME`
- Check that bucket exists in the specified region
- Ensure region matches `S3_REGION`

### Videos not loading
- Check S3 bucket CORS configuration (if needed)
- Verify video files are in the correct folder
- Check browser console for CORS errors
- Ensure video URLs are accessible (test in browser)

### CORS Configuration (if needed)

If videos don't load due to CORS, add this bucket policy:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

## Fallback to Local Files

If S3 is not configured or unavailable, the application will automatically fall back to serving videos from the local `static/reels/` folder.

## Security Best Practices

1. **Use Presigned URLs**: More secure than public buckets
2. **Rotate Credentials**: Regularly rotate AWS access keys
3. **Least Privilege**: Only grant necessary S3 permissions
4. **Use IAM Roles**: For EC2, use IAM roles instead of access keys
5. **Monitor Access**: Enable CloudTrail to monitor S3 access

## Using IAM Roles on EC2

If deploying on AWS EC2, you can use IAM roles instead of access keys:

1. Create IAM role with S3 permissions
2. Attach role to EC2 instance
3. Remove `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from `.env`
4. boto3 will automatically use the instance role

## Cost Considerations

- **Storage**: Pay for storage used
- **Requests**: Pay per GET request (very low cost)
- **Data Transfer**: Pay for data transfer out (first 100GB/month free)
- **Presigned URLs**: No additional cost

## Example .env Configuration

```bash
# MySQL Configuration
MYSQL_HOST=mysql
MYSQL_USER=reels_user
MYSQL_PASSWORD=your-password
MYSQL_DB=reels_db

# Flask Configuration
SECRET_KEY=your-secret-key

# S3 Configuration
S3_BUCKET_NAME=my-reels-bucket
S3_REGION=us-east-1
S3_REELS_FOLDER=reels/
S3_USE_PRESIGNED_URLS=true
S3_PRESIGNED_URL_EXPIRY=3600

# AWS Credentials (or use IAM role on EC2)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

