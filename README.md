# Instagram-Style Reels Application

A 2-tier Flask application with MySQL backend that displays video reels in an Instagram-like interface.

## Features

- 📱 Instagram-style reel display interface
- 🎥 Video playback with HTML5 video player
- ➕ Add new reels via web interface
- 🗑️ Delete reels
- 📱 Responsive design for mobile and desktop
- 🎨 Modern, gradient-based UI

## Architecture

This is a **2-tier application**:
- **Presentation Tier**: HTML/CSS/JavaScript frontend
- **Data Tier**: MySQL database storing reel URLs and metadata

Flask serves both the static frontend and provides REST API endpoints.

## Prerequisites

- Python 3.7+
- MySQL Server 5.7+ or 8.0+
- pip (Python package manager)

## Installation

1. **Clone or navigate to the project directory**

2. **Create a virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL database**
   - Make sure MySQL is running on your system
   - Create a `.env` file from the example:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with your MySQL credentials:
     ```
     MYSQL_HOST=localhost
     MYSQL_USER=root
     MYSQL_PASSWORD=your_password
     MYSQL_DB=reels_db
     ```

5. **Initialize the database**
   ```bash
   python init_db.py
   ```
   This will:
   - Create the database if it doesn't exist
   - Create the `reels` table
   - Insert sample reel data

## Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5001`
   
   Note: The app uses port 5001 by default to avoid conflicts with macOS AirPlay Receiver (which uses port 5000). You can change this by setting the `PORT` environment variable.

## API Endpoints

### GET `/api/reels`
Fetch all reels from the database.

**Response:**
```json
{
  "success": true,
  "reels": [
    {
      "id": 1,
      "url": "https://example.com/video.mp4",
      "title": "My Reel",
      "description": "Description here",
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "count": 1
}
```

### POST `/api/reels`
Add a new reel.

**Request Body:**
```json
{
  "url": "https://example.com/video.mp4",
  "title": "My Reel",
  "description": "Description here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reel added successfully",
  "reel_id": 1
}
```

### DELETE `/api/reels/<id>`
Delete a reel by ID.

**Response:**
```json
{
  "success": true,
  "message": "Reel deleted successfully"
}
```

## Database Schema

The `reels` table has the following structure:

```sql
CREATE TABLE reels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    title VARCHAR(200),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Project Structure

```
.
├── app.py                 # Main Flask application
├── init_db.py            # Database initialization script
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables example
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Stylesheet
    └── js/
        └── script.js     # JavaScript for frontend
```

## Adding Reels

You can add reels in two ways:

1. **Via Web Interface**: Click the "Add Reel" button and fill in the form
2. **Via API**: Use the POST endpoint to programmatically add reels

## Video URL Requirements

- URLs should point to video files (MP4, WebM, etc.)
- The videos should be accessible from the client's browser
- For testing, you can use sample video URLs from services like:
  - Google Cloud Storage sample videos
  - Your own video hosting service
  - Local server hosting videos

## Troubleshooting

### MySQL Connection Error
- Ensure MySQL server is running
- Verify credentials in `.env` file
- Check that the database exists (run `init_db.py`)

### Port Already in Use
- The app defaults to port 5001 to avoid macOS AirPlay conflicts
- You can change the port by setting the `PORT` environment variable: `PORT=5002 python app.py`

### Videos Not Playing
- Ensure video URLs are accessible
- Check CORS settings if videos are on different domains
- Verify video format is supported by the browser

## License

This project is open source and available for educational purposes.

