from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from database import DatabaseManager
from datetime import datetime, timedelta
import logging
import os
import json
from config import WEB, STORAGE
from unified_attendance import UnifiedAttendanceSystem

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
# Remove global db = DatabaseManager()

app.secret_key = WEB["secret_key"]
attendance_system = UnifiedAttendanceSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_system():
    try:
        attendance_system.start()
        return jsonify({"status": "started"})
    except Exception as e:
        logger.error(f"Error starting system: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_system():
    try:
        attendance_system.stop()
        return jsonify({"status": "stopped"})
    except Exception as e:
        logger.error(f"Error stopping system: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API Routes
@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    db = DatabaseManager()
    def decode_bytes(val):
        if isinstance(val, bytes):
            return val.decode('utf-8')
        return val
    def decode_confidence(val):
        if isinstance(val, bytes):
            try:
                return float(val.decode('utf-8'))
            except Exception:
                return None
        try:
            return float(val)
        except Exception:
            return None
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        attendance = db.get_attendance_for_date(date)
        # The columns are: name, timestamp, camera_id, confidence
        result = []
        for row in attendance:
            result.append({
                'name': decode_bytes(row[0]),
                'timestamp': decode_bytes(row[1]),
                'camera_id': decode_bytes(row[2]),
                'confidence': decode_confidence(row[3])
            })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting attendance: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    db = DatabaseManager()
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        analytics = db.get_analytics(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        return jsonify(analytics)
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/export', methods=['GET'])
def export_data():
    db = DatabaseManager()
    try:
        format_type = request.args.get('format', 'csv')
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        attendance = db.get_attendance_for_date(date)
        
        if format_type == 'csv':
            filename = f'attendance_{date}.csv'
            filepath = os.path.join(STORAGE["local"]["attendance_dir"], filename)
            
            with open(filepath, 'w') as f:
                f.write('Name,Timestamp,Camera ID,Confidence\n')
                for row in attendance:
                    f.write(f'{row[0]},{row[1]},{row[2]},{row[3]}\n')
            
            return send_file(filepath, as_attachment=True)
        
        elif format_type == 'excel':
            import pandas as pd
            filename = f'attendance_{date}.xlsx'
            filepath = os.path.join(STORAGE["local"]["attendance_dir"], filename)
            
            df = pd.DataFrame(attendance, columns=['Name', 'Timestamp', 'Camera ID', 'Confidence'])
            df.to_excel(filepath, index=False)
            
            return send_file(filepath, as_attachment=True)
        
        elif format_type == 'pdf':
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            filename = f'attendance_{date}.pdf'
            filepath = os.path.join(STORAGE["local"]["attendance_dir"], filename)
            
            c = canvas.Canvas(filepath, pagesize=letter)
            c.setFont("Helvetica", 12)
            
            y = 750
            c.drawString(50, y, f"Attendance Report for {date}")
            y -= 30
            
            for row in attendance:
                c.drawString(50, y, f"Name: {row[0]}")
                c.drawString(200, y, f"Time: {row[1]}")
                c.drawString(350, y, f"Camera: {row[2]}")
                c.drawString(450, y, f"Confidence: {row[3]:.2f}")
                y -= 20
                
                if y < 50:
                    c.showPage()
                    y = 750
            
            c.save()
            return send_file(filepath, as_attachment=True)
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/unauthorized', methods=['GET'])
def get_unauthorized_access():
    db = DatabaseManager()
    try:
        unauthorized = db.get_unauthorized_access()
        return jsonify(unauthorized)
    except Exception as e:
        logger.error(f"Error getting unauthorized access: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host=WEB["host"], port=WEB["port"], debug=WEB["debug"]) 