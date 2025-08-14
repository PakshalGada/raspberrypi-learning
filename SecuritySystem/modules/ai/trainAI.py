import os
import pickle
import face_recognition

def train_model(person_name):
    folder = f"data/photos/{person_name}"
    if not os.path.exists(folder):
        raise ValueError(f"Folder {folder} does not exist.")
    
    known_encodings = []
    known_names = []
    
    for file in os.listdir(folder):
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(folder, file)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(person_name)
    
    if not known_encodings:
        raise ValueError("No faces found in the photos.")
    
    os.makedirs('data/models', exist_ok=True)
    with open('data/models/known_faces.pickle', 'wb') as f:
        pickle.dump({'names': known_names, 'encodings': known_encodings}, f)
    
    return f"Training complete for {person_name}. Encodings saved to data/models/known_faces.pickle."