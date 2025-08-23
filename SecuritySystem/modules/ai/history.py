import os
import shutil
from datetime import datetime

BASE_DIR = os.path.join(os.path.dirname(__file__), "../../data")
FACE_CAPTURED = os.path.join(BASE_DIR, "faceCaptured")
FACE_DATA = os.path.join(BASE_DIR, "faceData")

os.makedirs(FACE_CAPTURED, exist_ok=True)
os.makedirs(FACE_DATA, exist_ok=True)



def get_all_photos_with_names():
    photos = []
    for date_folder in os.listdir(FACE_CAPTURED):
        date_path = os.path.join(FACE_CAPTURED, date_folder)
        if not os.path.isdir(date_path):
            continue

        for filename in os.listdir(date_path):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            person = filename.split("_")[0] if "_" in filename else "Unknown"

            try:
                time_str = filename.split("_")[1].split(".")[0] 
            except Exception:
                time_str = "00-00-00"

            try:
                dt = datetime.strptime(f"{date_folder} {time_str}", "%Y-%m-%d %H-%M-%S")
            except Exception:
                dt = datetime.min  

            rel_path = os.path.join("faceCaptured", date_folder, filename)

            photos.append({
                "path": rel_path,
                "person": person,
                "date": date_folder,
                "time": time_str.replace("-", ":"),
                "is_unknown": (person.lower() == "unknown"),
                "datetime": dt  
            })

    photos.sort(key=lambda x: x.get("datetime", datetime.min), reverse=True)
    return photos



def get_existing_people():
   
    if not os.path.exists(FACE_DATA):
        return []
    return [d for d in os.listdir(FACE_DATA) if os.path.isdir(os.path.join(FACE_DATA, d))]


def assign_photo(photo_rel_path, person_name, create_new=False):
   
    src = os.path.join(BASE_DIR, photo_rel_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"Photo not found: {src}")

    person_dir = os.path.join(FACE_DATA, person_name)
    os.makedirs(person_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dst = os.path.join(person_dir, f"{person_name}_{timestamp}.jpg")
    shutil.copy2(src, dst)

    return dst

