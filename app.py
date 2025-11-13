from flask import Flask, render_template, jsonify, request, session, url_for
import pymysql
import os
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import secrets

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

def get_db_connection():
    """Create and return a MySQL database connection"""
    return pymysql.connect(**MYSQL_CONFIG)

@app.route('/')
def index():
    """Main page to display reels"""
    return render_template('index.html')

@app.route('/api/reels', methods=['GET'])
def get_reels():
    """API endpoint to fetch all reels directly from static/reels folder"""
    try:
        # Get user session info
        user_id = session.get('user_id')
        views_count = session.get('views_count', 0)
        is_logged_in = user_id is not None
        
        # Get reels directly from static/reels folder
        reels_dir = os.path.join(app.static_folder, 'reels')
        reels_list = []
        
        if os.path.exists(reels_dir):
            video_files = [f for f in os.listdir(reels_dir) 
                          if f.lower().endswith(('.mp4', '.webm', '.mov', '.avi', '.mkv'))]
            
            for idx, filename in enumerate(video_files, start=1):
                # Extract title from filename (remove extension and clean up)
                title = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
                
                reel_dict = {
                    'id': idx,  # Use index as ID since we're not using database
                    'filename': filename,
                    'title': title,
                    'description': f'Video: {title}',
                    'url': url_for('static', filename=f'reels/{filename}'),
                    'created_at': datetime.now().isoformat()
                }
                reels_list.append(reel_dict)
        
        return jsonify({
            'success': True,
            'reels': reels_list,
            'count': len(reels_list),
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
    """API endpoint - reels are now read directly from folder, not stored in DB"""
    return jsonify({
        'success': False,
        'error': 'Reels are managed directly from the static/reels folder. Add video files to that folder.'
    }), 400

@app.route('/api/reels/<int:reel_id>', methods=['DELETE'])
def delete_reel(reel_id):
    """API endpoint - reels are now read directly from folder, not stored in DB"""
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if input is email (contains @) or username
        # Try both username and email
        cursor.execute(
            "SELECT id, username, email FROM users WHERE (username = %s OR email = %s) AND password_hash = %s",
            (username_or_email, username_or_email, password_hash)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
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

if __name__ == '__main__':
    import sys
    # Use port 5001 by default to avoid conflicts with AirPlay on macOS
    port = int(os.getenv('PORT', 5001))
    print(f"Starting Flask app on http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)

