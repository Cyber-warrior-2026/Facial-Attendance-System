import cv2
import numpy as np
import os
import time
from datetime import datetime
import threading
from face_recognition_manager import FaceRecognitionManager
from database import DatabaseManager
from config import CAMERAS, STORAGE, EMAIL
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class UnifiedAttendanceSystem:
    def __init__(self):
        self.face_manager = FaceRecognitionManager()
        self.db = DatabaseManager()
        self.running = False
        self.camera_thread = None
        self.marked_attendance = set()
        self._load_marked_attendance()

    def _load_marked_attendance(self):
        """Load today's marked attendance from database"""
        today = datetime.now().strftime('%Y-%m-%d')
        attendance = self.db.get_attendance_for_date(today)
        self.marked_attendance = {row[0] for row in attendance}  # row[0] is the name

    def send_email(self, to_email, subject, body, image_path=None):
        """Send email with optional image attachment"""
        msg = MIMEMultipart()
        msg["From"] = EMAIL["sender"]
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(image_path)}")
                msg.attach(part)

        try:
            server = smtplib.SMTP(EMAIL["smtp_server"], EMAIL["smtp_port"])
            server.starttls()
            server.login(EMAIL["sender"], EMAIL["password"])
            server.sendmail(EMAIL["sender"], to_email, msg.as_string())
            server.quit()
            print(f"Email sent successfully to {to_email}!")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def process_frame(self, frame, camera_id):
        """Process a single frame for face detection and recognition"""
        faces, gray = self.face_manager.detect_faces(frame)
        
        for (x, y, w, h) in faces:
            crop_img = frame[y:y+h, x:x+w]
            name, confidence = self.face_manager.recognize_face(crop_img)
            
            # Draw rectangle and display name
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y-40), (x+w, y), (0, 255, 0), -1)
            cv2.putText(frame, f"{name or 'Unknown'} ({confidence:.2f})", 
                       (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            if name and name not in self.marked_attendance:
                # Look up user_id and email for the recognized name
                db = DatabaseManager()
                db.cursor.execute("SELECT id, email FROM users WHERE name=?", (name,))
                user_row = db.cursor.fetchone()
                if user_row is not None:
                    user_id, user_email = user_row
                    db.mark_attendance(user_id, camera_id, confidence)
                    self.marked_attendance.add(name)
                    # --- Update analytics for today ---
                    today = datetime.now().strftime('%Y-%m-%d')
                    # Get today's attendance count and average confidence
                    db.cursor.execute("SELECT COUNT(*), AVG(confidence) FROM attendance WHERE date(timestamp) = date(?)", (today,))
                    count, avg_conf = db.cursor.fetchone()
                    # Get today's unauthorized attempts
                    db.cursor.execute("SELECT COUNT(*) FROM unauthorized_access WHERE date(timestamp) = date(?)", (today,))
                    unauthorized_count = db.cursor.fetchone()[0]
                    db.update_analytics(today, count, unauthorized_count, avg_conf if avg_conf is not None else 0.0)
                    # --- Email notification to user (if valid) ---
                    def is_valid_email(email):
                        import re
                        return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)
                    if user_email and is_valid_email(user_email):
                        self.send_email(
                            to_email=user_email,
                            subject="Attendance Marked Successfully",
                            body=f"Hello {name},\n\nYour attendance has been marked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
                        )
                    else:
                        print(f"Invalid or missing email for user {name}: {user_email}")
                    # --- Email notification to admin (if configured) ---
                    admin_email = EMAIL.get('admin')
                    if admin_email and is_valid_email(admin_email):
                        self.send_email(
                            to_email=admin_email,
                            subject=f"Attendance Marked for {name}",
                            body=f"Attendance for {name} was marked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Camera {camera_id}, Confidence {confidence:.2f})"
                        )
                db.close()
            elif not name and confidence < 0.6:  # Unauthorized access
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                image_path = os.path.join(STORAGE["local"]["unauthorized_dir"], f"unauthorized_{timestamp}.jpg")
                cv2.imwrite(image_path, frame)
                db = DatabaseManager()
                db.log_unauthorized_access(camera_id, image_path, confidence)
                db.close()

        return frame

    def camera_thread_func(self):
        """Thread function for processing camera feed"""
        video = cv2.VideoCapture(CAMERAS["ids"][0])  # Use first camera
        video.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERAS["resolution"][0])
        video.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERAS["resolution"][1])
        video.set(cv2.CAP_PROP_FPS, CAMERAS["fps"])

        while self.running:
            ret, frame = video.read()
            if not ret:
                print("Error: Could not capture video frame.")
                time.sleep(1)
                continue

            frame = self.process_frame(frame, CAMERAS["ids"][0])
            cv2.imshow("Facial Attendance System", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video.release()
        cv2.destroyAllWindows()

    def start(self):
        """Start the attendance system"""
        self.running = True
        self.camera_thread = threading.Thread(target=self.camera_thread_func)
        self.camera_thread.daemon = True
        self.camera_thread.start()

    def stop(self):
        """Stop the attendance system"""
        self.running = False
        if self.camera_thread:
            self.camera_thread.join()
        self.db.close()

if __name__ == "__main__":
    system = UnifiedAttendanceSystem()
    try:
        system.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        system.stop() 