import os

# Database Configuration
DATABASE_NAME = "attendance.db"

# Camera Configuration
CAMERA_IDS = [0]  # List of camera IDs to use
CAMERA_RESOLUTION = (640, 480)
FRAME_RATE = 30

# Face Detection Configuration
FACE_DETECTION_SCALE_FACTOR = 1.3
FACE_DETECTION_MIN_NEIGHBORS = 5
FACE_DETECTION_MIN_SIZE = (30, 30)

# Face Recognition Configuration
FACE_RECOGNITION_THRESHOLD = 0.6
FACE_RECOGNITION_MODEL = "haarcascade_frontalface_default.xml"

# Email Configuration
EMAIL_SETTINGS = {
    "ADMIN_EMAIL": "jsambhav335@gmail.com",
    "SENDER_EMAIL": "jsambhav335@gmail.com",
    "SENDER_PASSWORD": "cszrchmxtptmtsbw",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587
}

# File Storage Configuration
STORAGE_PATHS = {
    "ATTENDANCE_DIR": "Attendance",
    "UNAUTHORIZED_DIR": "Unauthorized_Access",
    "TRAINING_DATA_DIR": "data"
}

# Create necessary directories
for path in STORAGE_PATHS.values():
    os.makedirs(path, exist_ok=True)

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "attendance_system.log" 