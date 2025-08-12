import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DATABASE = {
    "type": "sqlite",  # or "postgresql", "mysql"
    "name": "attendance.db",
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", "")
}

# Camera Configuration
CAMERAS = {
    "ids": [0],  # List of camera IDs
    "resolution": (1280, 720),
    "fps": 30,
    "rotation": 0  # degrees to rotate image
}

# Face Detection Configuration
FACE_DETECTION = {
    "model": "haarcascade_frontalface_default.xml",
    "scale_factor": 1.3,
    "min_neighbors": 5,
    "min_size": (30, 30)
}

# Face Recognition Configuration
FACE_RECOGNITION = {
    "model": "face_recognition_model.h5",
    "threshold": 0.6,
    "embedding_size": 128
}

# Storage Configuration
STORAGE = {
    "local": {
        "attendance_dir": "Attendance",
        "unauthorized_dir": "Unauthorized_Access",
        "training_data_dir": "data"
    },
    "cloud": {
        "enabled": False,
        "provider": "aws",  # or "gcp", "azure"
        "bucket": os.getenv("CLOUD_BUCKET", ""),
        "region": os.getenv("CLOUD_REGION", "")
    }
}

# Email Configuration
EMAIL = {
    "admin": os.getenv("ADMIN_EMAIL", "jsambhav335@gmail.com"),
    "sender": os.getenv("SENDER_EMAIL", "jsambhav335@gmail.com"),
    "password": os.getenv("SENDER_PASSWORD", "cszrchmxtptmtsbw"),
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
}

# Web Interface Configuration
WEB = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": True,
    "secret_key": os.getenv("SECRET_KEY", "your-secret-key")
}

# Analytics Configuration
ANALYTICS = {
    "enabled": True,
    "retention_days": 30,
    "export_formats": ["csv", "excel", "pdf"]
}

# Create necessary directories
for path in STORAGE["local"].values():
    os.makedirs(path, exist_ok=True) 