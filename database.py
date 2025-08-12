import sqlite3
import threading
import os
from datetime import datetime, timedelta
import logging
import psycopg2
import mysql.connector
from config import DATABASE

# Removed the old Database class and its methods to avoid schema conflicts.

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._connect()
        self._initialize_database()

    def _connect(self):
        """Connect to the appropriate database"""
        if DATABASE["type"] == "sqlite":
            self.conn = sqlite3.connect(DATABASE["name"])
            self.cursor = self.conn.cursor()
        elif DATABASE["type"] == "postgresql":
            self.conn = psycopg2.connect(
                host=DATABASE["host"],
                port=DATABASE["port"],
                user=DATABASE["user"],
                password=DATABASE["password"],
                database=DATABASE["name"]
            )
            self.cursor = self.conn.cursor()
        elif DATABASE["type"] == "mysql":
            self.conn = mysql.connector.connect(
                host=DATABASE["host"],
                port=DATABASE["port"],
                user=DATABASE["user"],
                password=DATABASE["password"],
                database=DATABASE["name"]
            )
            self.cursor = self.conn.cursor()

    def _initialize_database(self):
        """Initialize the database and create necessary tables"""
        # Create users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                face_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')

        # Create attendance table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                camera_id INTEGER,
                confidence FLOAT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Create unauthorized_access table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unauthorized_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                camera_id TEXT,
                image_path TEXT,
                confidence REAL
            )
        ''')
        # Create analytics table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                total_attendance INTEGER,
                unauthorized_attempts INTEGER,
                average_confidence FLOAT
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
        except Exception as e:
            print(f"Error adding user: {e}")
            return None

    def mark_attendance(self, user_id, camera_id, confidence):
        """Mark attendance for a user"""
        self.cursor.execute(
            "INSERT INTO attendance (user_id, camera_id, confidence) VALUES (?, ?, ?)",
            (user_id, camera_id, confidence)
        )
        self.conn.commit()

    def log_unauthorized_access(self, camera_id, image_path, confidence):
        """Log unauthorized access attempt"""
        self.cursor.execute(
            "INSERT INTO unauthorized_access (camera_id, image_path, confidence) VALUES (?, ?, ?)",
            (camera_id, image_path, confidence)
        )
        self.conn.commit()

    def update_analytics(self, date, total_attendance, unauthorized_attempts, average_confidence):
        """Update analytics for a specific date"""
        self.cursor.execute('''
            INSERT INTO analytics (date, total_attendance, unauthorized_attempts, average_confidence)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                total_attendance = excluded.total_attendance,
                unauthorized_attempts = excluded.unauthorized_attempts,
                average_confidence = excluded.average_confidence
        ''', (date, total_attendance, unauthorized_attempts, average_confidence))
        self.conn.commit()

    def get_attendance_for_date(self, date):
        """Get attendance records for a specific date"""
        self.cursor.execute('''
            SELECT u.name, a.timestamp, a.camera_id, a.confidence
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE date(a.timestamp) = date(?)
            ORDER BY a.timestamp
        ''', (date,))
        return self.cursor.fetchall()

    def get_analytics(self, start_date, end_date):
        """Get analytics data for a date range"""
        self.cursor.execute('''
            SELECT date, total_attendance, unauthorized_attempts, average_confidence
            FROM analytics
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        ''', (start_date, end_date))
        return self.cursor.fetchall()

    def get_unauthorized_access(self):
        """Get all unauthorized access attempts"""
        self.cursor.execute('''
            SELECT * FROM unauthorized_access
            ORDER BY timestamp DESC
        ''')
        return self.cursor.fetchall()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close() 