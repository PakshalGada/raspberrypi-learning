import cv2
import face_recognition
import pickle
import os
import numpy as np
from picamera2 import Picamera2
import io
from PIL import Image
from datetime import datetime

DATASET_PATH = os.path.expanduser("/home/webbywonder/raspberrypi-learning/SecuritySystem/data/photos")
ENCODINGS_PATH = os.path.expanduser("/home/webbywonder/raspberrypi-learning/SecuritySystem/data/encodings.pickle")
CAPTURED_PATH = os.path.expanduser("/home/webbywonder/raspberrypi-learning/SecuritySystem/data/photos_captured")

def train_faces():
    known_encodings = []
    known_names = []
    
    print("Starting face training...")
    
    if not os.path.exists(DATASET_PATH):
        print(f"Dataset path does not exist: {DATASET_PATH}")
        return {"encodings": [], "names": []}
    
    for person_name in os.listdir(DATASET_PATH):
        person_dir = os.path.join(DATASET_PATH, person_name)
        if not os.path.isdir(person_dir):
            continue
            
        print(f"Processing images for: {person_name}")
        image_count = 0
        
        for image_file in os.listdir(person_dir):
            if image_file.endswith((".jpg", ".png", ".jpeg")):
                image_path = os.path.join(person_dir, image_file)
                try:
                    image = cv2.imread(image_path)
                    if image is None:
                        print(f"Could not load image: {image_path}")
                        continue
                        
                    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    boxes = face_recognition.face_locations(rgb, model="hog")
                    encodings = face_recognition.face_encodings(rgb, boxes)
                    
                    for encoding in encodings:
                        known_encodings.append(encoding)
                        known_names.append(person_name)
                        image_count += 1
                        
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
        
        print(f"Added {image_count} face encodings for {person_name}")
    
    data = {"encodings": known_encodings, "names": known_names}
    
    os.makedirs(os.path.dirname(ENCODINGS_PATH), exist_ok=True)
    with open(ENCODINGS_PATH, "wb") as f:
        f.write(pickle.dumps(data))
    
    print(f"Training complete! Total encodings: {len(known_encodings)}")
    return data

class FacialRecognitionCamera:
    def __init__(self, picam2_instance):
        self.picam2 = picam2_instance
        self.encodings_path = ENCODINGS_PATH
        self.captured_today = set()       
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists(self.encodings_path):
            try:
                with open(self.encodings_path, "rb") as f:
                    self.data = pickle.loads(f.read())
                print(f"Loaded {len(self.data['encodings'])} face encodings")
            except Exception as e:
                print(f"Error loading encodings: {e}")
                self.data = {"encodings": [], "names": []}
        else:
            print("No face encodings found. Please train faces first.")
            self.data = {"encodings": [], "names": []}

    def _save_person_image(self, image, name):
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today != self.current_date:
            self.captured_today = set()
            self.current_date = today

        if name in self.captured_today:
            return  

        save_dir = os.path.join(CAPTURED_PATH, today)
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = os.path.join(save_dir, f"{name}_{timestamp}.jpg")

        try:
            # Save the entire frame instead of cropped face
            cv2.imwrite(filename, image)
            print(f"[INFO] Saved full frame image for {name} at {filename}")
            self.captured_today.add(name)
        except Exception as e:
            print(f"Error saving image for {name}: {e}")

    def get_frame_with_recognition(self):
        try:
            frame = self.picam2.capture_array()
            
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                image = frame
            
            small_image = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small_image, cv2.COLOR_BGR2RGB)
            
            boxes = face_recognition.face_locations(rgb_small, model="hog")
            encodings = face_recognition.face_encodings(rgb_small, boxes)
            
            names = []
            for encoding in encodings:
                matches = face_recognition.compare_faces(
                    self.data["encodings"], encoding, tolerance=0.6
                )
                name = "Unknown"
                
                if True in matches:
                    matched_idxs = [i for (i, b) in enumerate(matches) if b]
                    counts = {}
                    for i in matched_idxs:
                        face_name = self.data["names"][i]
                        counts[face_name] = counts.get(face_name, 0) + 1
                    name = max(counts, key=counts.get)
                names.append(name)
            
            for ((top, right, bottom, left), name) in zip(boxes, names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)  
                
                cv2.rectangle(image, (left, top), (right, bottom), color, 2)
                
                cv2.rectangle(image, (left, top - 35), (right, top), color, cv2.FILLED)
                
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(image, name, (left + 6, top - 6), font, 0.6, (0, 0, 0), 1)

                # Save the entire frame with bounding boxes instead of cropped face
                if len(names) > 0:  # Only save if at least one face is detected
                    self._save_person_image(image, name)
            
            ret, jpeg = cv2.imencode('.jpg', image)
            if ret:
                return jpeg.tobytes()
            return None
            
        except Exception as e:
            print(f"Error in facial recognition: {e}")
            return None
