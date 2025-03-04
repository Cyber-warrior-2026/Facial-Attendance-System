import cv2  # Opening the webcam
import numpy as np  # For creating arrays
import os  # Reading and writing files
import pickle  # Used to save dataset

# Initialize Video Capture
video = cv2.VideoCapture(0)  # 0 for webcam

# Load Haar Cascade for face detection
facedetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

face_data = []  # List to store face images
i = 0

# Taking user input for name and email
name = input("Enter your name: ")
email = input("Enter your email: ")

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
        
        if len(face_data) < 50 and i % 10 == 0:  # Capture every 10th frame
            face_data.append(resize_img)  # Store face data
            
        # Draw rectangle and display count
        cv2.putText(frame, str(len(face_data)), org=(50, 50), fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=1, color=(50, 50, 255))
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 1)

    cv2.imshow("frame", frame)  # Show frame

    if cv2.waitKey(1) & 0xFF == ord('q') or len(face_data) == 50:  # Press 'q' to exit or when 50 images are collected
        break

# Release resources
video.release()
cv2.destroyAllWindows()

# Convert face data to numpy array and reshape
face_data = np.array(face_data)
face_data = face_data.reshape(50, -1)  # 50 images, flattened

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

# Save Face Data
face_data_file = "data/face_data.pkl"
if not os.path.exists(face_data_file):
    with open(face_data_file, "wb") as f:
        pickle.dump(face_data, f)
else:
    with open(face_data_file, "rb") as f:
        faces = pickle.load(f)
    faces = np.append(faces, face_data, axis=0)  # Append new faces
    with open(face_data_file, "wb") as f:
        pickle.dump(faces, f)

print("Face data, names, and emails saved successfully!")
