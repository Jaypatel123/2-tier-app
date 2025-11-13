"""
Quick script to test MySQL connection
Run this to verify your MySQL setup before running init_db.py
"""
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
}

print("Testing MySQL connection...")
print(f"Host: {config['host']}")
print(f"User: {config['user']}")
print(f"Password: {'*' * len(config['password']) if config['password'] else '(empty)'}")
print()

try:
    conn = mysql.connector.connect(**config)
    print("✅ SUCCESS! Connected to MySQL server")
    
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"MySQL Version: {version[0]}")
    
    cursor.close()
    conn.close()
    print("\nYou can now run: python init_db.py")
    
except mysql.connector.Error as err:
    print(f"❌ Connection failed!")
    print(f"Error: {err}")
    print()
    if err.errno == 2003:
        print("Troubleshooting:")
        print("1. Make sure MySQL is running: brew services start mysql")
        print("2. Check status: brew services list | grep mysql")
        print("3. Verify MySQL is listening: mysqladmin ping")
    elif err.errno == 1045:
        print("Troubleshooting:")
        print("1. On macOS Homebrew MySQL, root might not have a password")
        print("2. Create a .env file with: MYSQL_PASSWORD=''")
        print("3. Or set a MySQL password: mysqladmin -u root password 'yourpassword'")
    else:
        print(f"Error code: {err.errno}")
        print("Check your MySQL configuration")

