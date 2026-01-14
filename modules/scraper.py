import requests
from bs4 import BeautifulSoup
import threading
import json
import os

class GhostScraper:
    def __init__(self, sites_file="config/sites.json"):
        self.sites = self.load_sites(sites_file)
        self.results = []
        self.lock = threading.Lock()
        # Headers "Stealth" pour éviter les blocages (403)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def load_sites(self, filepath):
        """Charge la configuration des sites depuis le JSON"""
        if not os.path.exists(filepath):
            return {}
        with open(filepath, 'r') as f:
            return json.load(f)

    def extract_metadata(self, response, selectors):
        """Tente de récupérer la Bio, l'Avatar et la Location"""
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = {}
        if not selectors: return metadata

        try:
            # Extraction de la Bio
            if "bio" in selectors:
                sel = selectors["bio"]
                tag = soup.select_one(sel)
                if tag:
                    # Gère à la fois <meta content="..."> et <p>texte</p>
                    content = tag.get("content") if tag.get("content") else tag.get_text(strip=True)
                    metadata["Bio"] = content[:150] + "..." if content else "N/A"
            
            # Extraction de l'Avatar
            if "image" in selectors:
                sel = selectors["image"]
                tag = soup.select_one(sel)
                if tag and tag.get("content"):
                    metadata["Avatar"] = tag.get("content")

            # Extraction de la Localisation (si dispo)
            if "location" in selectors:
                sel = selectors["location"]
                tag = soup.select_one(sel)
                if tag:
                     metadata["Location"] = tag.get("content") if tag.get("content") else tag.get_text(strip=True)

        except Exception:
            pass # On ne veut pas faire planter le thread pour une méta manquante
        return metadata

    def check_site_worker(self, site_name, site_data, username, callback=None):
        """Vérifie un site unique (exécuté dans un thread)"""
        url = site_data["url"].format(username)
        try:
            # Timeout court (5s) pour garder de la vitesse
            response = requests.get(url, headers=self.headers, timeout=5)
            found = False

            # Logique 1 : Code HTTP 200
            if site_data.get("errorType") == "status_code":
                if response.status_code == 200:
                    found = True
            
            # (Ici on pourrait ajouter la Logique 2 pour les messages d'erreur textuels)

            if found:
                # Si trouvé, on enrichit les données (Scraping)
                meta = self.extract_metadata(response, site_data.get("selectors"))
                
                result_obj = {
                    "site": site_name,
                    "username": username, # <--- IMPORTANT : Quelle variante a été trouvée ?
                    "url": url,
                    "category": site_data.get("category", "unknown"),
                    "metadata": meta
                }
                
                with self.lock:
                    self.results.append(result_obj)
                
                # Mise à jour du Live Feed dans Streamlit
                if callback:
                    callback(f"✅ Trouvé : {site_name} ({username})")

        except Exception:
            pass # Silence en cas d'erreur de connexion

    def scan_username(self, username, callback_status=None):
        """Lance le scan multi-threadé pour UN pseudo donné"""
        # Note : On ne reset pas self.results ici pour permettre l'accumulation
        # si on appelle cette fonction plusieurs fois (pour les variantes)
        local_results = [] # Résultats juste pour ce tour
        threads = []
        
        for site_name, site_data in self.sites.items():
            t = threading.Thread(
                target=self.check_site_worker, 
                args=(site_name, site_data, username, callback_status)
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # On retourne la liste globale accumulée
        return self.results