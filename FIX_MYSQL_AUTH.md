# Fix MySQL Authentication Error (1045)

## Error Message
```
(1045, "Access denied for user 'root'@'localhost' (using password: YES)")
```

## Problem
The application is trying to connect to MySQL with incorrect credentials. This happens when:
1. Wrong username/password in `.env` file
2. Using `root` user when you should use `reels_user` (in Docker)
3. MySQL password doesn't match what's in `.env`

## Solutions

### Solution 1: If Running in Docker

When using Docker Compose, MySQL creates a user `reels_user` automatically. Update your `.env` file:

```bash
# .env file
MYSQL_HOST=mysql
MYSQL_USER=reels_user
MYSQL_PASSWORD=reels_password
MYSQL_DB=reels_db
```

**Important**: 
- `MYSQL_HOST` should be `mysql` (the Docker service name), not `localhost`
- `MYSQL_USER` should be `reels_user`, not `root`
- `MYSQL_PASSWORD` should match what's in docker-compose.yml

### Solution 2: If Running Locally (Not Docker)

#### Option A: Use Empty Password (Homebrew MySQL on macOS)

If you installed MySQL via Homebrew, root might not have a password:

```bash
# .env file
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=reels_db
```

#### Option B: Set MySQL Root Password

1. Connect to MySQL:
```bash
mysql -u root
```

2. Set password:
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'your-password';
FLUSH PRIVILEGES;
```

3. Update `.env`:
```bash
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DB=reels_db
```

#### Option C: Create a New MySQL User (Recommended)

1. Connect to MySQL:
```bash
mysql -u root
```

2. Create user and database:
```sql
CREATE DATABASE IF NOT EXISTS reels_db;
CREATE USER 'reels_user'@'localhost' IDENTIFIED BY 'reels_password';
GRANT ALL PRIVILEGES ON reels_db.* TO 'reels_user'@'localhost';
FLUSH PRIVILEGES;
```

3. Update `.env`:
```bash
MYSQL_HOST=localhost
MYSQL_USER=reels_user
MYSQL_PASSWORD=reels_password
MYSQL_DB=reels_db
```

4. Run database initialization:
```bash
python init_db.py
```

## Verify Configuration

### Step 1: Check Your .env File

```bash
cat .env | grep MYSQL
```

Should show:
```
MYSQL_HOST=mysql          # or localhost if not using Docker
MYSQL_USER=reels_user     # or root if using root
MYSQL_PASSWORD=reels_password
MYSQL_DB=reels_db
```

### Step 2: Test Connection

```bash
python test_connection.py
```

This will verify your MySQL credentials are correct.

### Step 3: Initialize Database

If connection works, initialize the database:

```bash
python init_db.py
```

## Common Scenarios

### Scenario 1: Using Docker Compose

**docker-compose.yml** creates:
- User: `reels_user`
- Password: `reels_password` (or from .env)
- Database: `reels_db`

**Your .env should have:**
```bash
MYSQL_HOST=mysql
MYSQL_USER=reels_user
MYSQL_PASSWORD=reels_password
MYSQL_DB=reels_db
```

### Scenario 2: Local MySQL (Homebrew)

**Default Homebrew MySQL:**
- User: `root`
- Password: (empty)

**Your .env should have:**
```bash
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=reels_db
```

### Scenario 3: Local MySQL (Installed via Installer)

**Usually has a password set during installation**

**Your .env should have:**
```bash
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-installation-password
MYSQL_DB=reels_db
```

## Quick Fix Commands

### For Docker:
```bash
# Stop containers
docker-compose down

# Update .env file with correct credentials
# Then restart
docker-compose up -d
```

### For Local MySQL:
```bash
# Test connection
python test_connection.py

# If it fails, reset MySQL password
mysql -u root
# Then run SQL commands from Solution 2 above
```

## After Fixing

1. Restart your Flask application
2. Try to register/login again
3. Check application logs for any remaining errors

## Still Having Issues?

1. Check MySQL is running:
   ```bash
   # Docker
   docker ps | grep mysql
   
   # Local
   brew services list | grep mysql
   # or
   mysqladmin ping
   ```

2. Verify database exists:
   ```bash
   mysql -u root -e "SHOW DATABASES;"
   ```

3. Check user permissions:
   ```bash
   mysql -u root -e "SELECT user, host FROM mysql.user;"
   ```

