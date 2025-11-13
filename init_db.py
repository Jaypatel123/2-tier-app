"""
Database initialization script
Run this script to create the database and table structure
"""
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
}

db_name = os.getenv('MYSQL_DB', 'reels_db')

try:
    # Connect to MySQL server
    print("Attempting to connect to MySQL server...")
    print(f"Host: {config['host']}, User: {config['user']}")
    
    # Try to connect, with better error handling
    try:
        conn = mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        if err.errno == 2003:
            print("\n❌ Error: Cannot connect to MySQL server.")
            print("   Make sure MySQL is running. Try: brew services start mysql")
            print("   Or check if MySQL is running: brew services list | grep mysql")
        elif err.errno == 1045:
            print("\n❌ Error: Access denied. Check your MySQL username and password.")
            print("   On macOS with Homebrew MySQL, root user might not have a password.")
            print("   Try setting MYSQL_PASSWORD='' in your .env file, or set a password.")
        else:
            print(f"\n❌ MySQL Error: {err}")
        raise
    
    print("✅ Successfully connected to MySQL server!")
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    print(f"Database '{db_name}' created or already exists")
    
    # Use the database
    cursor.execute(f"USE {db_name}")
    
    # Create users table
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_username (username),
        INDEX idx_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    cursor.execute(create_users_table)
    print("Table 'users' created or already exists")
    
    # Create reels table (updated to use local file paths)
    create_table_query = """
    CREATE TABLE IF NOT EXISTS reels (
        id INT AUTO_INCREMENT PRIMARY KEY,
        filename VARCHAR(500) NOT NULL,
        title VARCHAR(200),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    cursor.execute(create_table_query)
    print("Table 'reels' created or already exists")
    
    # Insert sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM reels")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Get list of video files from static/reels folder
        import os
        reels_dir = os.path.join(os.path.dirname(__file__), 'static', 'reels')
        sample_reels = []
        
        if os.path.exists(reels_dir):
            video_files = [f for f in os.listdir(reels_dir) if f.endswith(('.mp4', '.webm', '.mov'))]
            for filename in video_files:
                # Extract title from filename (remove extension and clean up)
                title = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
                sample_reels.append((filename, title, f"Video: {title}"))
        
        if sample_reels:
            insert_query = "INSERT INTO reels (filename, title, description) VALUES (%s, %s, %s)"
            cursor.executemany(insert_query, sample_reels)
            print(f"Inserted {len(sample_reels)} reels from static/reels folder")
        else:
            print("No video files found in static/reels folder")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\nDatabase initialization completed successfully!")
    print(f"You can now start the Flask application with: python app.py")
    
except mysql.connector.Error as err:
    print(f"Error: {err}")
except Exception as e:
    print(f"Unexpected error: {e}")

