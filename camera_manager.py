import cv2
import threading
import queue
import time
from config import CAMERA_IDS, CAMERA_RESOLUTION, FRAME_RATE

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.frame_queues = {}
        self.running = False
        self.threads = []

    def start(self):
        """Start all camera feeds"""
        self.running = True
        for camera_id in CAMERA_IDS:
            self._start_camera(camera_id)

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
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_RESOLUTION[0])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_RESOLUTION[1])
        camera.set(cv2.CAP_PROP_FPS, FRAME_RATE)

        if not camera.isOpened():
            print(f"Error: Could not open camera {camera_id}")
            return

        self.cameras[camera_id] = camera
        self.frame_queues[camera_id] = queue.Queue(maxsize=2)
        
        thread = threading.Thread(target=self._camera_thread, args=(camera_id,))
        thread.daemon = True
        thread.start()
        self.threads.append(thread)

    def _camera_thread(self, camera_id):
        """Thread function for capturing frames from a camera"""
        while self.running:
            ret, frame = self.cameras[camera_id].read()
            if not ret:
                print(f"Error: Could not capture frame from camera {camera_id}")
                time.sleep(1)
                continue

            if not self.frame_queues[camera_id].full():
                self.frame_queues[camera_id].put(frame)

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