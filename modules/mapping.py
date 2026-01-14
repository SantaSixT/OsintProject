import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

def generate_map(results):
    """
    Prend les résultats du scan, cherche les villes dans les métadonnées,
    et génère une carte Folium avec des marqueurs.
    """
    # 1. Initialisation du Géocodeur
    # user_agent est OBLIGATOIRE pour ne pas être bloqué par Nominatim
    geolocator = Nominatim(user_agent="ghost_tracker_project_v2")
    
    # Création de la carte (Centrée par défaut sur l'Europe/Monde)
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    
    locations_found = 0
    processed_cities = set() # Pour éviter de placer 10 marqueurs au même endroit (ex: 10 fois Paris)

    print("[*] Génération de la carte tactique...")

    for res in results:
        meta = res.get('metadata', {})
        # On cherche la clé "Location" ou "Lieu"
        location_str = meta.get('Location')
        
        # Si on a une ville et qu'on ne l'a pas encore traitée pour ce site exact
        if location_str:
            try:
                # Géocodage (Ville -> Latitude/Longitude)
                location = geolocator.geocode(location_str, timeout=5)
                
                if location:
                    locations_found += 1
                    
                    # Création du contenu de la bulle (Popup)
                    popup_html = f"""
                    <b>{res['username']}</b><br>
                    Service: {res['site']}<br>
                    📍 {location_str}
                    """
                    
                    # Ajout du marqueur
                    folium.Marker(
                        [location.latitude, location.longitude],
                        popup=popup_html,
                        tooltip=f"{res['site']} - {location_str}",
                        icon=folium.Icon(color="red", icon="info-sign")
                    ).add_to(m)
                    
                    # Pause de politesse pour l'API (Rate Limit)
                    time.sleep(1)
                    
            except (GeocoderTimedOut, Exception) as e:
                print(f"[!] Erreur géo pour {location_str}: {e}")

    return m, locations_found