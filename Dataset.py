import cv2  # Opening the webcam
import numpy as np  # For creating arrays
import os  # Reading and writing files
import pickle  # Used to save dataset
import tensorflow as tf
from config import FACE_RECOGNITION
from database import DatabaseManager

# Initialize Video Capture
video = cv2.VideoCapture(0)  # 0 for webcam

# Load Haar Cascade for face detection
facedetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# Always use the CNN embedding model architecture for extracting embeddings
def get_embedding_model():
    return tf.keras.Sequential([
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(50, 50, 3)),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(FACE_RECOGNITION["embedding_size"], activation='relu')
    ])

face_model = get_embedding_model()

face_data = []  # List to store face embeddings
i = 0

# Taking user input for name and email
name = input("Enter your name: ")
email = input("Enter your email: ")

# Insert user into users table if not already present
user_db = DatabaseManager()
user_db.cursor.execute("SELECT id FROM users WHERE name=? AND email=?", (name, email))
user_row = user_db.cursor.fetchone()
if user_row is None:
    user_db.cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    user_db.conn.commit()
    print(f"User '{name}' added to users table.")
else:
    print(f"User '{name}' already exists in users table.")
user_db.close()

# Webcam loop for face detection and saving data
while True:
    ret, frame = video.read()  # Capture frame-by-frame
    if not ret:
        break  # Stop if webcam fails

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    faces = facedetect.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)  # Detect faces
    
    for (x, y, w, h) in faces:
        crop_img = frame[y:y+h, x:x+w]  # Crop detected face
        resize_img = cv2.resize(crop_img, (50, 50))  # Resize to 50x50 pixels
        norm_img = resize_img.astype('float32') / 255.0
        norm_img = np.expand_dims(norm_img, axis=0)
        embedding = face_model.predict(norm_img)[0]  # Get 128-dim embedding
        
        if len(face_data) < 50 and i % 10 == 0:  # Capture every 10th frame
            face_data.append(embedding)  # Store face embedding
            
        # Draw rectangle and display count
        cv2.putText(frame, str(len(face_data)), org=(50, 50), fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=1, color=(50, 50, 255))
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 1)

    cv2.imshow("frame", frame)  # Show frame

    if cv2.waitKey(1) & 0xFF == ord('q') or len(face_data) == 50:  # Press 'q' to exit or when 50 embeddings are collected
        break

# Release resources
video.release()
cv2.destroyAllWindows()

# Convert face data to numpy array
face_data = np.array(face_data)  # shape: (50, 128)

# Create data directory if it doesn't exist
if not os.path.exists("data"):
    os.makedirs("data")

# Save Names Data
names_file = "data/names.pkl"
if not os.path.exists(names_file):
    names = [name] * 50  # Store name 50 times
    with open(names_file, "wb") as f:
        pickle.dump(names, f)
else:
    with open(names_file, "rb") as f:
        names = pickle.load(f)
    names += [name] * 50  # Append new name data
    with open(names_file, "wb") as f:
        pickle.dump(names, f)

# Save Emails Data (New column)
emails_file = "data/emails.pkl"
if not os.path.exists(emails_file):
    emails = [email] * 50  # Store email 50 times
    with open(emails_file, "wb") as f:
        pickle.dump(emails, f)
else:
    with open(emails_file, "rb") as f:
        emails = pickle.load(f)
    emails += [email] * 50  # Append new email data
    with open(emails_file, "wb") as f:
        pickle.dump(emails, f)

# Save Face Data (embeddings)
face_data_file = "data/face_data.pkl"
if not os.path.exists(face_data_file):
    with open(face_data_file, "wb") as f:
        pickle.dump(face_data, f)
else:
    with open(face_data_file, "rb") as f:
        faces = pickle.load(f)
    faces = np.append(faces, face_data, axis=0)  # Append new embeddings
    with open(face_data_file, "wb") as f:
        pickle.dump(faces, f)

print("Face embeddings, names, and emails saved successfully!")
