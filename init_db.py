"""
Database initialization script
Run this script to create the database and table structure
"""
import mysql.connector
import os

# Database configuration
config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
}

db_name = os.getenv('MYSQL_DB', 'reels_db')

try:
    # Connect to MySQL server
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    print(f"Database '{db_name}' created or already exists")
    
    # Use the database
    cursor.execute(f"USE {db_name}")
    
    # Create reels table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS reels (
        id INT AUTO_INCREMENT PRIMARY KEY,
        url VARCHAR(500) NOT NULL,
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
        sample_reels = [
            ("https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", "Big Buck Bunny", "A large and lovable rabbit deals with three tiny bullies."),
            ("https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4", "Elephant's Dream", "The story of two strange characters exploring a surreal world."),
            ("https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4", "For Bigger Blazes", "A fun video for bigger blazes."),
            ("https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4", "For Bigger Escapes", "An escape adventure video."),
            ("https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4", "For Bigger Fun", "A video for bigger fun."),
        ]
        
        insert_query = "INSERT INTO reels (url, title, description) VALUES (%s, %s, %s)"
        cursor.executemany(insert_query, sample_reels)
        print(f"Inserted {len(sample_reels)} sample reels")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\nDatabase initialization completed successfully!")
    print(f"You can now start the Flask application with: python app.py")
    
except mysql.connector.Error as err:
    print(f"Error: {err}")
except Exception as e:
    print(f"Unexpected error: {e}")

