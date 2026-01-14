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
        
        # Headers "Stealth" équilibrés
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def load_sites(self, filepath):
        if not os.path.exists(filepath): return {}
        with open(filepath, 'r') as f: return json.load(f)

    def extract_metadata(self, soup, selectors):
        metadata = {}
        if not selectors: return metadata
        try:
            if "bio" in selectors:
                sel = selectors["bio"]
                tag = soup.select_one(sel)
                if tag:
                    content = tag.get("content") if tag.get("content") else tag.get_text(strip=True)
                    metadata["Bio"] = content[:150] + "..." if content else "N/A"
            if "image" in selectors:
                sel = selectors["image"]
                tag = soup.select_one(sel)
                if tag and tag.get("content"):
                    metadata["Avatar"] = tag.get("content")
            if "location" in selectors:
                sel = selectors["location"]
                tag = soup.select_one(sel)
                if tag:
                     metadata["Location"] = tag.get("content") if tag.get("content") else tag.get_text(strip=True)
        except: pass
        return metadata

    def check_site_worker(self, site_name, site_data, username, callback=None):
        url = site_data["url"].format(username)
        try:
            # On autorise les redirections pour détecter les pages de login
            response = requests.get(url, headers=self.headers, timeout=5, allow_redirects=True)
            found = False
            
            # --- DIAGNOSTIC (S'affiche dans le terminal VSCode) ---
            # print(f"[DEBUG] {site_name} -> Code: {response.status_code} | URL: {response.url}")

            # 1. FILTRE : Redirection vers Login (Classique Instagram/Facebook/Twitter)
            # Si l'URL finale contient "login", c'est qu'on a été bloqué -> On considère non trouvé
            if "login" in response.url.lower() or "signin" in response.url.lower():
                found = False
            
            # 2. FILTRE : Code HTTP
            elif site_data.get("errorType") == "status_code":
                if response.status_code == 200:
                    found = True
            
            # 3. FILTRE : Message d'erreur dans le texte (Soft 404)
            elif site_data.get("errorType") == "message":
                if response.status_code == 200:
                    error_msg = site_data.get("errorMsg")
                    # Si le message d'erreur n'est PAS dans la page, c'est bon
                    if error_msg and error_msg not in response.text:
                        found = True

            # --- SUCCÈS ---
            if found:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check Ultime : Si le titre est vide ou suspect (trop court), méfiance
                page_title = soup.title.string.strip() if soup.title else ""
                
                # Si le titre est juste "Instagram" ou "Twitter" sans le pseudo, c'est souvent un faux positif
                # Mais on est souple : on ne rejette que si c'est flagrant
                if len(page_title) < 15 and site_name in ["Instagram", "Twitter"] and username not in page_title:
                    pass # On ignore ce résultat (Faux Positif probable)
                else:
                    # C'est validé !
                    meta = self.extract_metadata(soup, site_data.get("selectors"))
                    
                    result_obj = {
                        "site": site_name,
                        "username": username,
                        "url": url,
                        "category": site_data.get("category", "unknown"),
                        "metadata": meta
                    }
                    
                    with self.lock:
                        self.results.append(result_obj)
                    
                    if callback:
                        callback(f"✅ Trouvé : {site_name} ({username})")

        except Exception as e:
            # print(f"[Err] {site_name}: {e}")
            pass 

    def scan_username(self, username, callback_status=None):
        threads = []
        # On ne reset pas self.results pour permettre d'accumuler les variantes
        for site_name, site_data in self.sites.items():
            t = threading.Thread(
                target=self.check_site_worker, 
                args=(site_name, site_data, username, callback_status)
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        return self.results