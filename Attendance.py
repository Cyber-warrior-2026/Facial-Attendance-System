import cv2
import numpy as np
import os
import csv
import time
import pickle
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from sklearn.neighbors import KNeighborsClassifier
from datetime import datetime

# Load webcam
video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Ensure required data files exist
names_file = "data/names.pkl"
faces_file = "data/face_data.pkl"
emails_file = "data/emails.pkl"

if not os.path.exists(names_file) or not os.path.exists(faces_file) or not os.path.exists(emails_file):
    print("Error: Required data files not found! Please collect training data first.")
    exit()

# Load stored face data and labels
with open(names_file, 'rb') as w:
    LABELS = pickle.load(w)

with open(faces_file, 'rb') as f:
    FACES = pickle.load(f)

with open(emails_file, 'rb') as e:
    EMAILS = pickle.load(e)

# Train KNN classifier
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)

# Ensure necessary folders exist
os.makedirs("Attendance", exist_ok=True)
os.makedirs("Unauthorized_Access", exist_ok=True)

# Email Configuration
ADMIN_EMAIL = "jsambhav335@gmail.com"
SENDER_EMAIL = "jsambhav335@gmail.com"
SENDER_PASSWORD = "cszrchmxtptmtsbw"  # Use App Password for security

# Function to send email with an optional image attachment
def send_email(to_email, subject, body, image_path=None):
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach image if provided
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(image_path)}")
            msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"📧 Email sent successfully to {to_email}!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# Attendance tracking
date = datetime.now().strftime("%d-%m-%Y")
attendance_csv = f"Attendance/Attendance_{date}.csv"

# Create CSV file if not exists
if not os.path.isfile(attendance_csv):
    with open(attendance_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['NAME', 'TIME'])

# Read existing attendance
marked_attendance = set()
with open(attendance_csv, "r", newline="") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    for row in reader:
        marked_attendance.add(row[0])

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
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Draw rectangle around face and display name
        cv2.rectangle(frame, (x, y, x+w, y+h), (0, 255, 0), 2)
        cv2.rectangle(frame, (x, y-40, x+w, y), (0, 255, 0), -1)
        cv2.putText(frame, output, (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Mark attendance if user is recognized
        if output not in marked_attendance:
            marked_attendance.add(output)

            # Save attendance
            with open(attendance_csv, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([output, timestamp])

            print(f"✅ Attendance recorded for: {output} at {timestamp}")

            index = LABELS.index(output)
            email = EMAILS[index]
            send_email(email, "Attendance Marked Successfully",
                       f"Hello {output},\n\nYour attendance has been marked at {timestamp}.")

    cv2.imshow("Face Recognition Attendance", frame)
    
    k = cv2.waitKey(1)
    if k == ord('q'):
        break

# Convert CSV to Excel when the program exits
attendance_excel = f"Attendance/Attendance_{date}.xlsx"
try:
    df = pd.read_csv(attendance_csv)  # Read CSV file
    df.to_excel(attendance_excel, index=False)  # Convert to Excel
    print(f"📂 Attendance saved as Excel file: {attendance_excel}")
except Exception as e:
    print(f"❌ Error converting CSV to Excel: {e}")

video.release()
cv2.destroyAllWindows()
