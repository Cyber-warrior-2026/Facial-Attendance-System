from flask import Flask, render_template, jsonify, request, send_file
from database import DatabaseManager
from datetime import datetime
import os
from config import STORAGE_PATHS

app = Flask(__name__)
db = DatabaseManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance = db.get_attendance_for_date(date)
    return jsonify([{'name': row[0], 'timestamp': row[1]} for row in attendance])

@app.route('/api/users', methods=['GET'])
def get_users():
    users = db.get_all_users()
    return jsonify([{'id': row[0], 'name': row[1], 'email': row[2]} for row in users])

@app.route('/api/unauthorized', methods=['GET'])
def get_unauthorized_access():
    unauthorized = db.get_unauthorized_access()
    return jsonify([{'timestamp': row[1], 'image_path': row[2]} for row in unauthorized])

@app.route('/api/attendance/export', methods=['GET'])
def export_attendance():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance = db.get_attendance_for_date(date)
    
    # Create CSV file
    filename = f'attendance_{date}.csv'
    filepath = os.path.join(STORAGE_PATHS['ATTENDANCE_DIR'], filename)
    
    with open(filepath, 'w') as f:
        f.write('Name,Timestamp\n')
        for row in attendance:
            f.write(f'{row[0]},{row[1]}\n')
    
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 