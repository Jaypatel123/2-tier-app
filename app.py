from flask import Flask, render_template, jsonify, request, session, url_for
import pymysql
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib
import secrets
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# MySQL Configuration
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DB', 'reels_db'),
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': False
}

# S3 Configuration
S3_CONFIG = {
    'bucket_name': os.getenv('S3_BUCKET_NAME', ''),
    'region': os.getenv('S3_REGION', 'us-east-1'),
    'folder_prefix': os.getenv('S3_REELS_FOLDER', 'reels/'),
    'use_presigned_urls': os.getenv('S3_USE_PRESIGNED_URLS', 'false').lower() == 'true',
    'presigned_url_expiry': int(os.getenv('S3_PRESIGNED_URL_EXPIRY', '3600'))  # Default 1 hour
}

# Initialize S3 client
s3_client = None
if S3_CONFIG['bucket_name']:
    try:
        s3_client = boto3.client(
            's3',
            region_name=S3_CONFIG['region'],
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
    except Exception as e:
        print(f"Warning: Could not initialize S3 client: {e}")
        s3_client = None

def get_db_connection():
    """Create and return a MySQL database connection"""
    try:
        return pymysql.connect(**MYSQL_CONFIG)
    except pymysql.Error as e:
        error_code, error_msg = e.args
        if error_code == 1045:
            print(f"MySQL Authentication Error: {error_msg}")
            print(f"Attempted connection with user: {MYSQL_CONFIG['user']}")
            print("Please check your MySQL credentials in .env file:")
            print(f"  MYSQL_USER={MYSQL_CONFIG['user']}")
            print(f"  MYSQL_PASSWORD={'*' * len(MYSQL_CONFIG['password']) if MYSQL_CONFIG['password'] else '(empty)'}")
            print("\nIf using Docker, ensure you're using the correct user:")
            print("  MYSQL_USER=reels_user (not root)")
            print("  MYSQL_PASSWORD=reels_password")
        raise

@app.route('/')
def index():
    """Main page to display reels"""
    return render_template('index.html')

def get_s3_video_url(filename):
    """Generate S3 URL for a video file (presigned or public)"""
    if not s3_client or not S3_CONFIG['bucket_name']:
        return None
    
    # Construct S3 key (path in bucket)
    s3_key = f"{S3_CONFIG['folder_prefix'].rstrip('/')}/{filename}"
    
    try:
        if S3_CONFIG['use_presigned_urls']:
            # Generate presigned URL (temporary, secure)
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': S3_CONFIG['bucket_name'],
                    'Key': s3_key
                },
                ExpiresIn=S3_CONFIG['presigned_url_expiry']
            )
            print(f"Generated presigned URL for {filename}")
            return url
        else:
            # Generate public URL (if bucket is public)
            url = f"https://{S3_CONFIG['bucket_name']}.s3.{S3_CONFIG['region']}.amazonaws.com/{s3_key}"
            print(f"Generated public URL for {filename}")
            return url
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print(f"Error generating S3 URL for {filename}: {error_code} - {error_msg}")
        if error_code == 'AccessDenied':
            print(f"Access denied to S3 object: {s3_key}. Check IAM permissions.")
        elif error_code == 'NoSuchKey':
            print(f"Object not found in S3: {s3_key}")
        return None
    except Exception as e:
        print(f"Unexpected error generating S3 URL for {filename}: {e}")
        return None

def list_s3_videos():
    """List all video files from S3 bucket"""
    if not s3_client or not S3_CONFIG['bucket_name']:
        print("S3 client not initialized or bucket name not set")
        return []
    
    video_extensions = ('.mp4', '.webm', '.mov', '.avi', '.mkv')
    video_files = []
    
    try:
        prefix = S3_CONFIG['folder_prefix'].rstrip('/') + '/'
        print(f"Listing S3 objects in bucket '{S3_CONFIG['bucket_name']}' with prefix '{prefix}'")
        paginator = s3_client.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket=S3_CONFIG['bucket_name'], Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    filename = os.path.basename(key)
                    if filename.lower().endswith(video_extensions):
                        video_files.append(filename)
            elif 'KeyCount' in page and page['KeyCount'] == 0:
                print(f"No objects found in S3 bucket with prefix '{prefix}'")
        
        print(f"Found {len(video_files)} video files in S3")
        return sorted(video_files)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print(f"Error listing S3 videos: {error_code} - {error_msg}")
        if error_code == 'AccessDenied':
            print("Access denied to S3 bucket. Check IAM permissions.")
        elif error_code == 'NoSuchBucket':
            print(f"Bucket '{S3_CONFIG['bucket_name']}' does not exist.")
        return []
    except NoCredentialsError:
        print("Error: AWS credentials not found")
        return []
    except Exception as e:
        print(f"Unexpected error listing S3 videos: {e}")
        return []

def list_local_videos():
    """List all video files from local static/reels folder (fallback)"""
    reels_dir = os.path.join(app.static_folder, 'reels')
    video_files = []
    
    if os.path.exists(reels_dir):
        video_files = [f for f in os.listdir(reels_dir) 
                      if f.lower().endswith(('.mp4', '.webm', '.mov', '.avi', '.mkv'))]
    
    return sorted(video_files)

@app.route('/api/reels', methods=['GET'])
def get_reels():
    """API endpoint to fetch all reels from S3 bucket or local folder"""
    try:
        # Get user session info
        user_id = session.get('user_id')
        views_count = session.get('views_count', 0)
        is_logged_in = user_id is not None
        
        reels_list = []
        
        # Try to get videos from S3 first, fallback to local
        if s3_client and S3_CONFIG['bucket_name']:
            video_files = list_s3_videos()
            source = 'S3'
            # If S3 returns no videos, fallback to local
            if not video_files:
                print("No videos found in S3, falling back to local files")
                video_files = list_local_videos()
                source = 'local'
        else:
            video_files = list_local_videos()
            source = 'local'
        
        for idx, filename in enumerate(video_files, start=1):
            # Extract title from filename (remove extension and clean up)
            title = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
            
            # Get URL based on source
            if source == 'S3':
                video_url = get_s3_video_url(filename)
                if not video_url:
                    continue  # Skip if we can't generate URL
            else:
                video_url = url_for('static', filename=f'reels/{filename}')
            
            reel_dict = {
                'id': idx,
                'filename': filename,
                'title': title,
                'description': f'Video: {title}',
                'url': video_url,
                'created_at': datetime.now().isoformat(),
                'source': source
            }
            reels_list.append(reel_dict)
        
        return jsonify({
            'success': True,
            'reels': reels_list,
            'count': len(reels_list),
            'source': source,
            'user': {
                'is_logged_in': is_logged_in,
                'views_count': views_count,
                'views_remaining': max(0, 10 - views_count) if not is_logged_in else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reels', methods=['POST'])
def add_reel():
    """API endpoint - reels are now read from S3 bucket or local folder"""
    if s3_client and S3_CONFIG['bucket_name']:
        return jsonify({
            'success': False,
            'error': 'Reels are managed in S3 bucket. Upload video files to the S3 bucket.'
        }), 400
    else:
        return jsonify({
            'success': False,
            'error': 'Reels are managed directly from the static/reels folder. Add video files to that folder.'
        }), 400

@app.route('/api/reels/<int:reel_id>', methods=['DELETE'])
def delete_reel(reel_id):
    """API endpoint - reels are now read from S3 bucket or local folder"""
    if s3_client and S3_CONFIG['bucket_name']:
        return jsonify({
            'success': False,
            'error': 'Reels are managed in S3 bucket. Delete video files from the S3 bucket.'
        }), 400
    else:
        return jsonify({
            'success': False,
            'error': 'Reels are managed directly from the static/reels folder. Remove video files from that folder.'
        }), 400

@app.route('/api/track-view', methods=['POST'])
def track_view():
    """Track when a user views a reel"""
    try:
        # Increment view count for non-logged-in users
        if not session.get('user_id'):
            views_count = session.get('views_count', 0)
            views_count += 1
            session['views_count'] = views_count
            
            return jsonify({
                'success': True,
                'views_count': views_count,
                'views_remaining': max(0, 10 - views_count),
                'requires_login': views_count >= 10
            })
        else:
            # Logged in users have unlimited views
            return jsonify({
                'success': True,
                'views_count': None,
                'views_remaining': None,
                'requires_login': False
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Username, email, and password are required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
        except pymysql.Error as e:
            return jsonify({
                'success': False,
                'error': f'Database connection failed: {str(e)}. Please check your MySQL configuration.'
            }), 500
        
        try:
            # Check if username or email already exists
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Username or email already exists'
                }), 400
            
            # Create user
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (%s, %s, %s, %s)",
                (username, email, password_hash, datetime.now())
            )
            conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            conn.close()
        except pymysql.Error as e:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}'
            }), 500
        
        # Set session
        session['user_id'] = user_id
        session['username'] = username
        session['views_count'] = 0  # Reset view count after login
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': user_id,
                'username': username
            }
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint - accepts both username and email"""
    try:
        data = request.get_json()
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({
                'success': False,
                'error': 'Username/Email and password are required'
            }), 400
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
        except pymysql.Error as e:
            return jsonify({
                'success': False,
                'error': f'Database connection failed: {str(e)}. Please check your MySQL configuration.'
            }), 500
        
        try:
            # Check if input is email (contains @) or username
            # Try both username and email
            cursor.execute(
                "SELECT id, username, email FROM users WHERE (username = %s OR email = %s) AND password_hash = %s",
                (username_or_email, username_or_email, password_hash)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()
        except pymysql.Error as e:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}'
            }), 500
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid username/email or password'
            }), 401
        
        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['views_count'] = 0  # Reset view count after login
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    user_id = session.get('user_id')
    views_count = session.get('views_count', 0)
    
    return jsonify({
        'success': True,
        'is_logged_in': user_id is not None,
        'user': {
            'id': user_id,
            'username': session.get('username')
        } if user_id else None,
        'views_count': views_count,
        'views_remaining': max(0, 10 - views_count) if not user_id else None
    })

@app.route('/api/debug/s3', methods=['GET'])
def debug_s3():
    """Debug endpoint to check S3 configuration and connectivity"""
    debug_info = {
        's3_configured': bool(S3_CONFIG['bucket_name']),
        'bucket_name': S3_CONFIG['bucket_name'],
        'region': S3_CONFIG['region'],
        'folder_prefix': S3_CONFIG['folder_prefix'],
        'use_presigned_urls': S3_CONFIG['use_presigned_urls'],
        's3_client_initialized': s3_client is not None,
        'aws_credentials_set': bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))
    }
    
    if s3_client and S3_CONFIG['bucket_name']:
        try:
            # Test bucket access
            s3_client.head_bucket(Bucket=S3_CONFIG['bucket_name'])
            debug_info['bucket_access'] = 'OK'
            
            # Try to list objects
            prefix = S3_CONFIG['folder_prefix'].rstrip('/') + '/'
            response = s3_client.list_objects_v2(
                Bucket=S3_CONFIG['bucket_name'],
                Prefix=prefix,
                MaxKeys=1
            )
            debug_info['list_objects'] = 'OK'
            debug_info['objects_found'] = response.get('KeyCount', 0)
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            debug_info['bucket_access'] = f'ERROR: {error_code} - {error_msg}'
            debug_info['list_objects'] = f'ERROR: {error_code} - {error_msg}'
        except Exception as e:
            debug_info['bucket_access'] = f'ERROR: {str(e)}'
            debug_info['list_objects'] = f'ERROR: {str(e)}'
    
    return jsonify(debug_info)

if __name__ == '__main__':
    import sys
    # Use port 5001 by default to avoid conflicts with AirPlay on macOS
    port = int(os.getenv('PORT', 5001))
    print(f"Starting Flask app on http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)

