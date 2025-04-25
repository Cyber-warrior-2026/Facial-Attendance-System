import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="attendance.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the database and create necessary tables"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        # Create users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                face_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create attendance table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Create unauthorized_access table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unauthorized_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT
            )
        ''')

        self.conn.commit()

    def add_user(self, name, email, face_data):
        """Add a new user to the database"""
        try:
            self.cursor.execute(
                "INSERT INTO users (name, email, face_data) VALUES (?, ?, ?)",
                (name, email, face_data)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def mark_attendance(self, user_id):
        """Mark attendance for a user"""
        self.cursor.execute(
            "INSERT INTO attendance (user_id) VALUES (?)",
            (user_id,)
        )
        self.conn.commit()

    def get_user_by_face_data(self, face_data):
        """Get user by face data"""
        self.cursor.execute(
            "SELECT id, name, email FROM users WHERE face_data = ?",
            (face_data,)
        )
        return self.cursor.fetchone()

    def get_attendance_for_date(self, date):
        """Get attendance records for a specific date"""
        self.cursor.execute('''
            SELECT u.name, a.timestamp 
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE date(a.timestamp) = date(?)
            ORDER BY a.timestamp
        ''', (date,))
        return self.cursor.fetchall()

    def log_unauthorized_access(self, image_path):
        """Log unauthorized access attempt"""
        self.cursor.execute(
            "INSERT INTO unauthorized_access (image_path) VALUES (?)",
            (image_path,)
        )
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close() 