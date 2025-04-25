import cv2
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import pickle
import os
from config import (
    FACE_DETECTION_SCALE_FACTOR,
    FACE_DETECTION_MIN_NEIGHBORS,
    FACE_DETECTION_MIN_SIZE,
    FACE_RECOGNITION_MODEL,
    FACE_RECOGNITION_THRESHOLD,
    STORAGE_PATHS
)

class FaceRecognitionManager:
    def __init__(self):
        self.face_detector = cv2.CascadeClassifier(FACE_RECOGNITION_MODEL)
        self.knn = KNeighborsClassifier(n_neighbors=5)
        self.face_data = []
        self.labels = []
        self._load_training_data()

    def _load_training_data(self):
        """Load face data and labels from the database"""
        data_dir = STORAGE_PATHS["TRAINING_DATA_DIR"]
        faces_file = os.path.join(data_dir, "face_data.pkl")
        labels_file = os.path.join(data_dir, "labels.pkl")

        if os.path.exists(faces_file) and os.path.exists(labels_file):
            with open(faces_file, 'rb') as f:
                self.face_data = pickle.load(f)
            with open(labels_file, 'rb') as l:
                self.labels = pickle.load(l)
            
            if len(self.face_data) > 0:
                self.knn.fit(self.face_data, self.labels)

    def detect_faces(self, frame):
        """Detect faces in a frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=FACE_DETECTION_SCALE_FACTOR,
            minNeighbors=FACE_DETECTION_MIN_NEIGHBORS,
            minSize=FACE_DETECTION_MIN_SIZE
        )
        return faces, gray

    def recognize_face(self, face_img):
        """Recognize a face from an image"""
        if len(self.face_data) == 0:
            return None, 0

        face_img = cv2.resize(face_img, (50, 50))
        face_img = face_img.flatten().reshape(1, -1)
        
        distances, indices = self.knn.kneighbors(face_img, n_neighbors=1)
        confidence = 1.0 / (1.0 + distances[0][0])
        
        if confidence < FACE_RECOGNITION_THRESHOLD:
            return None, confidence
            
        return self.labels[indices[0][0]], confidence

    def add_face_data(self, face_img, label):
        """Add new face data for training"""
        face_img = cv2.resize(face_img, (50, 50))
        face_img = face_img.flatten()
        
        self.face_data.append(face_img)
        self.labels.append(label)
        
        # Retrain the classifier
        self.knn.fit(self.face_data, self.labels)
        
        # Save the updated data
        self._save_training_data()

    def _save_training_data(self):
        """Save face data and labels to files"""
        data_dir = STORAGE_PATHS["TRAINING_DATA_DIR"]
        os.makedirs(data_dir, exist_ok=True)
        
        with open(os.path.join(data_dir, "face_data.pkl"), 'wb') as f:
            pickle.dump(self.face_data, f)
        with open(os.path.join(data_dir, "labels.pkl"), 'wb') as l:
            pickle.dump(self.labels, l) 