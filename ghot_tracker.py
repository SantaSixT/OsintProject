import requests
from bs4 import BeautifulSoup
import time
import random
import threading
import json
import argparse
import sys
import os

# --- CONFIGURATION & CONSTANTES ---
BANNER = """
   ________                  __  
  /  _____/  __ __   ______ /  |_ 
 /   \  ___ |  |  \ /  ___/|   __\\
 \    \_\  \|  |  / \___ \ |  |  
  \______  /|____/ /____  >|__|  
         \/             \/       
  v3.0 - OSINT Swiss Army Knife
"""

class GhostTracker:
    def __init__(self, username, sites_file="sites.json"):
        self.username = username
        self.results = []
        self.print_lock = threading.Lock()
        self.sites = self.load_sites(sites_file)
        
        # Headers furtifs
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def load_sites(self, filepath):
        """Charge la base de données des sites depuis le JSON"""
        if not os.path.exists(filepath):
            print(f"[!] Erreur : Fichier {filepath} introuvable.")
            sys.exit(1)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[!] Erreur : Format JSON invalide dans {filepath}.")
            sys.exit(1)

    def check_site(self, site_name, site_data):
        url = site_data["url"].format(self.username)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            found = False

            # Logique 1 : Basée sur le code HTTP (404 = pas trouvé)
            if site_data.get("errorType") == "status_code":
                if response.status_code == 200:
                    found = True
            
            # Logique 2 : Basée sur un message d'erreur dans le texte (pour les soft 404)
            elif site_data.get("errorType") == "message":
                if response.status_code == 200:
                    error_msg = site_data.get("errorMsg")
                    if error_msg not in response.text:
                        found = True

            if found:
                with self.print_lock:
                    print(f"[+] FOUND: {site_name:<15} -> {url}")
                self.results.append({"site": site_name, "url": url, "status": "FOUND"})
        
        except Exception:
            pass # Silence is golden in CLI tools

    def run(self):
        print(f"[*] Analyse du profil : {self.username}")
        print(f"[*] Sites chargés : {len(self.sites)}")
        
        threads = []
        for site_name, site_data in self.sites.items():
            t = threading.Thread(target=self.check_site, args=(site_name, site_data))
            threads.append(t)
            t.start()
            time.sleep(0.05) # Petit délai pour éviter le flood

        for t in threads:
            t.join()

    def save_report(self, filename):
        """Exporte les résultats en JSON"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"\n[V] Rapport sauvegardé dans : {filename}")

# --- MAIN ---
if __name__ == "__main__":
    print(BANNER)
    
    # Gestion des arguments CLI (Le standard pro)
    parser = argparse.ArgumentParser(description="Outil OSINT de recherche de pseudos.")
    parser.add_argument("-u", "--username", required=True, help="Le pseudo à rechercher")
    parser.add_argument("-o", "--output", help="Nom du fichier pour sauvegarder le rapport (ex: report.json)")
    parser.add_argument("-d", "--database", default="sites.json", help="Fichier JSON des sites cibles")
    
    args = parser.parse_args()

    tracker = GhostTracker(args.username, args.database)
    tracker.run()
    
    if args.output:
        tracker.save_report(args.output)
    else:
        print("\n[*] Terminé. Utilisez -o pour sauvegarder.")