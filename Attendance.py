import cv2
import numpy as np
import os
import csv
import time
import pickle
import pandas as pd  # Import pandas for CSV to Excel conversion
from sklearn.neighbors import KNeighborsClassifier
from datetime import datetime

# Load webcam
video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Ensure required data files exist
names_file = "data/names.pkl"
faces_file = "data/face_data.pkl"

if not os.path.exists(names_file) or not os.path.exists(faces_file):
    print("Error: Required data files not found! Please collect training data first.")
    exit()

# Load stored face data and labels
with open(names_file, 'rb') as w:
    LABELS = pickle.load(w)

with open(faces_file, 'rb') as f:
    FACES = pickle.load(f)

# Train KNN classifier
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)

# Load background image
background_path = "background.webp"
imgbackground = cv2.imread(background_path)

if imgbackground is None:
    print("Error: Unable to load background image. Check the file path.")
    exit()

# Ensure attendance folder exists
if not os.path.exists("Attendance"):
    os.makedirs("Attendance")

# CSV file column headers
COL_NAMES = ['NAME', 'TIME']

# Get today's date
date = datetime.now().strftime("%d-%m-%Y")
attendance_csv = f"Attendance/Attendance_{date}.csv"
attendance_excel = f"Attendance/Attendance_{date}.xlsx"  # Excel file path

# Create CSV file if it does not exist
if not os.path.isfile(attendance_csv):
    with open(attendance_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(COL_NAMES)

# Read existing attendance to prevent duplicate marking for the same day
marked_attendance = set()
with open(attendance_csv, "r", newline="") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header row
    for row in reader:
        marked_attendance.add(row[0])  # Store names already marked for the day

while True:
    ret, frame = video.read()
    if not ret:
        print("Error: Could not capture video frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        crop_img = frame[y:y+h, x:x+w]
        resize_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)

        # Predict name
        output = knn.predict(resize_img)[0]

        ts = time.time()
        timestamp = datetime.fromtimestamp(ts).strftime("%H:%M:%S")

        # Draw rectangle around face and display name
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.rectangle(frame, (x, y-40), (x+w, y), (0, 255, 0), -1)
        cv2.putText(frame, output, (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Mark attendance only if not already marked today
        if output not in marked_attendance:
            marked_attendance.add(output)
            with open(attendance_csv, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([output, timestamp])
            print(f"✅ Attendance recorded for: {output} at {timestamp}")

    # Check if background image is large enough
    if imgbackground.shape[0] >= 642 and imgbackground.shape[1] >= 695:
        imgbackground[162:162+480, 55:55+640] = frame
    else:
        print("Error: Background image is too small to fit the video frame.")
        break

    cv2.imshow("Face Recognition Attendance", imgbackground)
    
    k = cv2.waitKey(1)
    if k == ord('q'):  # Exit program
        break

# Convert CSV to Excel when the program exits
try:
    df = pd.read_csv(attendance_csv)  # Read CSV file
    df.to_excel(attendance_excel, index=False)  # Convert to Excel
    print(f"📂 Attendance saved as Excel file: {attendance_excel}")
except Exception as e:
    print(f"❌ Error converting CSV to Excel: {e}")

video.release()
cv2.destroyAllWindows()
