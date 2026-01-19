from PIL import Image
from PIL.ExifTags import TAGS
import requests
from io import BytesIO

def get_exif_data(image_url):
    """Télécharge une image et extrait les métadonnées cachées"""
    if not image_url or "http" not in image_url:
        return None

    try:
        response = requests.get(image_url, timeout=3)
        img = Image.open(BytesIO(response.content))
        
        # Extraction EXIF
        exif_data = img._getexif()
        if not exif_data:
            return None

        result = {}
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag, tag)
            # On filtre les données binaires trop lourdes
            if isinstance(value, bytes):
                continue
            result[decoded] = str(value)
            
        return result
    except Exception:
        return None