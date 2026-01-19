import face_recognition
import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image

class FaceHunter:
    def __init__(self):
        self.known_encoding = None
        self.has_face = False

    def load_target_image(self, uploaded_file):
        """Charge l'image cible et apprend le visage"""
        try:
            # Conversion Streamlit upload -> Image lisible
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            # Conversion BGR (OpenCV) -> RGB (Face Recognition)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Détection du visage
            encodings = face_recognition.face_encodings(rgb_img)
            
            if len(encodings) > 0:
                self.known_encoding = encodings[0]
                self.has_face = True
                return True, f"Visage détecté et encodé ! (128 points biométriques)"
            else:
                return False, "Aucun visage détecté sur cette photo."
                
        except Exception as e:
            return False, f"Erreur de lecture : {e}"

    def compare_with_url(self, url):
        """Télécharge un avatar en ligne et le compare avec la cible"""
        if not self.has_face or not url:
            return None

        try:
            # Téléchargement de l'avatar distant
            response = requests.get(url, timeout=3)
            img_arr = np.array(Image.open(BytesIO(response.content)))
            
            # Détection visage distant
            unknown_encodings = face_recognition.face_encodings(img_arr)
            
            if len(unknown_encodings) > 0:
                # Comparaison (Distance euclidienne)
                # Plus la distance est petite, plus c'est la même personne
                # 0.6 est le seuil standard. 0.4 est très strict.
                distance = face_recognition.face_distance([self.known_encoding], unknown_encodings[0])[0]
                match_score = (1 - distance) * 100 # Conversion en % de ressemblance
                
                is_match = distance < 0.6
                return {
                    "match": is_match,
                    "score": round(match_score, 2),
                    "distance": round(distance, 4)
                }
            
            return {"error": "Pas de visage sur l'avatar distant"}

        except Exception as e:
            return {"error": "Image illisible"}