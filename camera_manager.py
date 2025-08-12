import cv2
import threading
import queue
import time
import numpy as np
from config import CAMERAS

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.frame_queues = {}
        self.running = False
        self.threads = []
        self._initialize_cameras()

    def _initialize_cameras(self):
        """Initialize all cameras"""
        for camera_id in CAMERAS["ids"]:
            self._start_camera(camera_id)

    def start(self):
        """Start all camera feeds"""
        self.running = True
        for camera_id in CAMERAS["ids"]:
            thread = threading.Thread(target=self._camera_thread, args=(camera_id,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def stop(self):
        """Stop all camera feeds"""
        self.running = False
        for thread in self.threads:
            thread.join()
        for camera in self.cameras.values():
            camera.release()

    def _start_camera(self, camera_id):
        """Start a single camera feed"""
        camera = cv2.VideoCapture(camera_id)
        
        # Set camera properties
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERAS["resolution"][0])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERAS["resolution"][1])
        camera.set(cv2.CAP_PROP_FPS, CAMERAS["fps"])
        
        if not camera.isOpened():
            print(f"Error: Could not open camera {camera_id}")
            return

        self.cameras[camera_id] = camera
        self.frame_queues[camera_id] = queue.Queue(maxsize=2)

    def _camera_thread(self, camera_id):
        """Thread function for capturing frames from a camera"""
        while self.running:
            ret, frame = self.cameras[camera_id].read()
            if not ret:
                print(f"Error: Could not capture frame from camera {camera_id}")
                time.sleep(1)
                continue

            # Rotate frame if needed
            if CAMERAS["rotation"] != 0:
                frame = self._rotate_frame(frame, CAMERAS["rotation"])

            if not self.frame_queues[camera_id].full():
                self.frame_queues[camera_id].put(frame)

    def _rotate_frame(self, frame, angle):
        """Rotate frame by specified angle"""
        height, width = frame.shape[:2]
        center = (width/2, height/2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(frame, rotation_matrix, (width, height))

    def get_frame(self, camera_id):
        """Get the latest frame from a specific camera"""
        if camera_id not in self.frame_queues:
            return None

        try:
            return self.frame_queues[camera_id].get_nowait()
        except queue.Empty:
            return None

    def get_all_frames(self):
        """Get frames from all cameras"""
        frames = {}
        for camera_id in self.cameras:
            frame = self.get_frame(camera_id)
            if frame is not None:
                frames[camera_id] = frame
        return frames

    def get_camera_status(self):
        """Get status of all cameras"""
        status = {}
        for camera_id in self.cameras:
            status[camera_id] = {
                "connected": self.cameras[camera_id].isOpened(),
                "fps": self.cameras[camera_id].get(cv2.CAP_PROP_FPS),
                "resolution": (
                    int(self.cameras[camera_id].get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(self.cameras[camera_id].get(cv2.CAP_PROP_FRAME_HEIGHT))
                )
            }
        return status 