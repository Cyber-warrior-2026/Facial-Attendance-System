import cv2
import numpy as np
import tensorflow as tf
from sklearn.neighbors import KNeighborsClassifier
import pickle
import os
from config import FACE_DETECTION, FACE_RECOGNITION, STORAGE
from sklearn.preprocessing import LabelEncoder

class FaceRecognitionManager:
    def __init__(self):
        self.face_detector = cv2.CascadeClassifier(FACE_DETECTION["model"])
        self.embedding_model = self._load_embedding_model()
        self.classifier_model = self._load_classifier_model()
        self.face_data = []
        self.labels = []
        self._load_training_data()

    def _load_embedding_model(self):
        # Always create a new CNN embedding model (not trained for recognition)
        model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(50, 50, 3)),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(FACE_RECOGNITION["embedding_size"], activation='relu')
        ])
        return model

    def _load_classifier_model(self):
        # Load the trained classifier model if it exists
        if os.path.exists(FACE_RECOGNITION["model"]):
            return tf.keras.models.load_model(FACE_RECOGNITION["model"])
        else:
            # Return a dummy model if not trained yet
            return None

    def _load_training_data(self):
        data_dir = STORAGE["local"]["training_data_dir"]
        faces_file = os.path.join(data_dir, "face_data.pkl")
        names_file = os.path.join(data_dir, "names.pkl")

        if os.path.exists(faces_file) and os.path.exists(names_file):
            with open(faces_file, 'rb') as f:
                self.face_data = pickle.load(f)
            with open(names_file, 'rb') as l:
                self.labels = pickle.load(l)

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=FACE_DETECTION["scale_factor"],
            minNeighbors=FACE_DETECTION["min_neighbors"],
            minSize=FACE_DETECTION["min_size"]
        )
        return faces, gray

    def recognize_face(self, face_img):
        if len(self.face_data) == 0 or self.classifier_model is None:
            return None, 0

        # Preprocess the face image
        face_img = cv2.resize(face_img, (50, 50))
        face_img = face_img.astype('float32') / 255.0
        face_img = np.expand_dims(face_img, axis=0)

        # Get face embedding
        embedding = self.embedding_model.predict(face_img)[0]
        embedding = np.expand_dims(embedding, axis=0)

        # Classify embedding
        probs = self.classifier_model.predict(embedding)[0]
        predicted_index = np.argmax(probs)
        confidence = probs[predicted_index]
        name = self.labels[predicted_index]

        if confidence < FACE_RECOGNITION["threshold"]:
            return None, confidence

        return name, confidence

    def add_face_data(self, face_img, label):
        face_img = cv2.resize(face_img, (50, 50))
        face_img = face_img.astype('float32') / 255.0
        face_img = np.expand_dims(face_img, axis=0)
        embedding = self.embedding_model.predict(face_img)[0]
        self.face_data.append(embedding)
        self.labels.append(label)
        self._save_training_data()

    def _save_training_data(self):
        data_dir = STORAGE["local"]["training_data_dir"]
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, "face_data.pkl"), 'wb') as f:
            pickle.dump(self.face_data, f)
        with open(os.path.join(data_dir, "names.pkl"), 'wb') as l:
            pickle.dump(self.labels, l)

    def train_model(self, epochs=10):
        if len(self.face_data) < 2:
            print("Not enough data to train the model")
            return
        X = np.array(self.face_data)
        y = np.array(self.labels)
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(FACE_RECOGNITION["embedding_size"],)),
            tf.keras.layers.Dense(len(set(y_encoded)), activation='softmax')
        ])
        model.compile(optimizer='adam',
                     loss='sparse_categorical_crossentropy',
                     metrics=['accuracy'])
        model.fit(X, y_encoded, epochs=epochs, validation_split=0.2)
        model.save(FACE_RECOGNITION["model"])
        print("Model trained and saved as", FACE_RECOGNITION["model"])

if __name__ == "__main__":
    frm = FaceRecognitionManager()
    frm.train_model(epochs=20)
    print("Model trained and saved as", FACE_RECOGNITION["model"]) 