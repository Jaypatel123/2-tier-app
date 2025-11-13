from flask import Flask, render_template, jsonify, request
from flask_mysqldb import MySQL
import os
from datetime import datetime

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'reels_db')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def index():
    """Main page to display reels"""
    return render_template('index.html')

@app.route('/api/reels', methods=['GET'])
def get_reels():
    """API endpoint to fetch all reels"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM reels ORDER BY created_at DESC")
        reels = cursor.fetchall()
        cursor.close()
        
        # Convert datetime objects to strings for JSON serialization
        for reel in reels:
            if 'created_at' in reel and reel['created_at']:
                reel['created_at'] = reel['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'reels': reels,
            'count': len(reels)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reels', methods=['POST'])
def add_reel():
    """API endpoint to add a new reel"""
    try:
        data = request.get_json()
        url = data.get('url')
        title = data.get('title', '')
        description = data.get('description', '')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO reels (url, title, description, created_at) VALUES (%s, %s, %s, %s)",
            (url, title, description, datetime.now())
        )
        mysql.connection.commit()
        reel_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Reel added successfully',
            'reel_id': reel_id
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reels/<int:reel_id>', methods=['DELETE'])
def delete_reel(reel_id):
    """API endpoint to delete a reel"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM reels WHERE id = %s", (reel_id,))
        mysql.connection.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        
        if affected_rows == 0:
            return jsonify({
                'success': False,
                'error': 'Reel not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Reel deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

