import cv2
import numpy as np
import os
import csv
import time
import pickle
import pandas as pd
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from sklearn.neighbors import KNeighborsClassifier
from datetime import datetime
from geopy.distance import geodesic

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

# Define authorized location (latitude, longitude)
AUTHORIZED_LOCATION = (26.20085149761659, 78.1828866089955)  # Change to your actual location
RADIUS_LIMIT = 0.5  # 500 meters radius

# Email Configuration
ADMIN_EMAIL = "jsambhav335@gmail.com"
SENDER_EMAIL = "jsambhav335@gmail.com"
SENDER_PASSWORD = "cszrchmxtptmtsbw"  # Use App Password for security

# Function to get user's current location
def get_current_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        if "loc" in data:
            lat, lon = map(float, data["loc"].split(","))
            return (lat, lon)
    except Exception as e:
        print(f"⚠️ Error getting location: {e}")
    return None

# Function to check if user is within the allowed location
def is_within_location(user_location):
    if user_location:
        distance = geodesic(user_location, AUTHORIZED_LOCATION).km
        print(f"📏 Distance to authorized location: {distance:.2f} km")
        return distance <= RADIUS_LIMIT
    return False

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

# Check user's location before allowing attendance
user_location = get_current_location()
if user_location:
    print(f"🌍 Your detected location: {user_location}")

if not is_within_location(user_location):
    print("🚨 Access Denied: You are outside the authorized location!")

    # Send alert to admin
    send_email(ADMIN_EMAIL, "🚨 Unauthorized Location Access Attempt!",
               f"An access attempt was made from outside the authorized location at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
    
    exit()

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

        if output not in LABELS:
            print(f"🚨 Unauthorized Access Attempt Detected!")

            # Save image of unauthorized person
            unknown_img_path = f"Unauthorized_Access/Intruder_{timestamp}.jpg"
            cv2.imwrite(unknown_img_path, crop_img)

            # Ensure the image is saved before sending
            time.sleep(2)  # Give time for the file to be written
            if os.path.exists(unknown_img_path):
                print(f"📷 Intruder image saved at {unknown_img_path}")

                # Send alert email with the intruder's image
                send_email(ADMIN_EMAIL, "🚨 Unauthorized Access Alert!",
                           f"An unauthorized person tried to access the system at {timestamp}. Please check the attached image.",
                           unknown_img_path)
                print("📧 Intruder image email sent to admin.")
            else:
                print("❌ Error: Intruder image not saved, email not sent.")

            continue  # Skip further processing for unknown person

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

video.release()
cv2.destroyAllWindows()
