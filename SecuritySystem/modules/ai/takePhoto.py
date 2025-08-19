import os
import time
from datetime import datetime
from picamera2 import Picamera2

def sanitize_folder_name(name):

    import re
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    sanitized = sanitized.strip('. ')
    return sanitized if sanitized else 'unknown_user'

def take_photo_for_user(user_name, picam2_instance=None):

    try:
        if picam2_instance is None:
            picam2 = Picamera2()
            picam2.configure(picam2.create_still_configuration())
            picam2.start()
            should_stop = True
        else:
            picam2 = picam2_instance
            should_stop = False
        
        sanitized_name = sanitize_folder_name(user_name)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        user_photos_dir = os.path.join('data', 'photos', sanitized_name)
        os.makedirs(user_photos_dir, exist_ok=True)
        
        filename = os.path.join(user_photos_dir, f'photo_{timestamp}.jpg')
        
        picam2.capture_file(filename)
        
        if should_stop:
            picam2.stop()
            picam2.close()
        
        print(f"Photo saved for {user_name}: {filename}")
        return filename
        
    except Exception as e:
        print(f"Error taking photo: {e}")
        return None

def list_user_photos(user_name):
    
    sanitized_name = sanitize_folder_name(user_name)
    user_photos_dir = os.path.join('data', 'photos', sanitized_name)
    
    if not os.path.exists(user_photos_dir):
        return []
    
    photos = []
    for filename in os.listdir(user_photos_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            photos.append(os.path.join(user_photos_dir, filename))
    
    photos.sort(key=lambda x: os.path.getctime(x), reverse=True)
    return photos

def create_photos_directory():
    photos_dir = os.path.join('data', 'photos')
    os.makedirs(photos_dir, exist_ok=True)
    return photos_dir

if __name__ == "__main__":
    test_user = input("Enter user name for test photo: ").strip()
    if test_user:
        create_photos_directory()
        photo_path = take_photo_for_user(test_user)
        if photo_path:
            print(f"Test photo captured successfully: {photo_path}")
        else:
            print("Failed to capture test photo")
    else:
        print("No user name provided")
