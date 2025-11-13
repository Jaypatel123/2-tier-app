#!/bin/bash
# Script to fix MySQL version mismatch by reinitializing with fresh data

echo "⚠️  WARNING: This will remove your existing MySQL data directory!"
echo "   All existing databases will be lost!"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Stopping MySQL service..."
brew services stop mysql

echo ""
echo "Backing up old data directory..."
BACKUP_DIR="/opt/homebrew/var/mysql_backup_$(date +%Y%m%d_%H%M%S)"
if [ -d "/opt/homebrew/var/mysql" ]; then
    mv /opt/homebrew/var/mysql "$BACKUP_DIR"
    echo "Backup created at: $BACKUP_DIR"
fi

echo ""
echo "Initializing MySQL with fresh data directory..."
mysqld --initialize-insecure --user=$(whoami) --datadir=/opt/homebrew/var/mysql

echo ""
echo "Starting MySQL service..."
brew services start mysql

echo ""
echo "Waiting for MySQL to start..."
sleep 5

echo ""
echo "Testing connection..."
mysqladmin ping

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ MySQL is now running!"
    echo "   You can now run: python init_db.py"
else
    echo ""
    echo "❌ MySQL failed to start. Check logs: tail -f /opt/homebrew/var/mysql/*.err"
fi

