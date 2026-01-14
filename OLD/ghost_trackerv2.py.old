import requests
from bs4 import BeautifulSoup
import time
import random
import threading
import json
import argparse
import sys
import os
from googlesearch import search  # pip install googlesearch-python

# --- CONFIGURATION ---
BANNER = """
   ________                  __     
  /  _____/  __ __   ______ /  |_   
 /   \  ___ |  |  \ /  ___/|   __\\  
 \    \_\  \|  |  / \___ \ |  |     
  \______  /|____/ /____  >|__|     
         \/             \/          
  v4.0 - Data Enrichment & Dorking
"""

class GhostTracker:
    def __init__(self, username, sites_file="sites.json", use_permutations=False):
        self.original_username = username
        self.usernames_to_check = [username]
        
        # Module 1 : Permutations (Si activé)
        if use_permutations:
            self.generate_permutations()
            
        self.results = []
        self.print_lock = threading.Lock()
        self.sites = self.load_sites(sites_file)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def load_sites(self, filepath):
        if not os.path.exists(filepath):
            print(f"[!] Erreur : {filepath} manquant.")
            return {}
        with open(filepath, 'r') as f:
            return json.load(f)

    def generate_permutations(self):
        """Génère des variantes simples du pseudo"""
        base = self.original_username
        variants = [
            base,
            base + "1",
            base + "123",
            base + "_official",
            base + ".dev",
            base.replace("e", "3").replace("a", "4") # Leet speak basique
        ]
        # On dédoublonne
        self.usernames_to_check = list(set(variants))
        print(f"[*] Mode Permutation activé : {len(self.usernames_to_check)} variantes générées.")

    def extract_metadata(self, response, selectors):
        """Module 2 : Data Enrichment (Scraping Intelligent)"""
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = {}
        
        if not selectors:
            return None

        # Extraction de la BIO
        if "bio" in selectors:
            try:
                # Supporte les balises <meta> et les classes CSS
                sel = selectors["bio"]
                if "meta" in sel:
                    tag = soup.select_one(sel)
                    if tag and tag.get("content"):
                        metadata["Bio"] = tag["content"][:60] + "..." # On coupe si trop long
                else:
                    tag = soup.select_one(sel)
                    if tag:
                        metadata["Bio"] = tag.get_text(strip=True)[:60] + "..."
            except: pass

        # Extraction de l'IMAGE
        if "image" in selectors:
            try:
                tag = soup.select_one(selectors["image"])
                if tag and tag.get("content"):
                    metadata["Avatar"] = tag["content"]
            except: pass

        return metadata

    def check_site(self, site_name, site_data, username):
        url = site_data["url"].format(username)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            found = False

            if site_data.get("errorType") == "status_code":
                if response.status_code == 200:
                    found = True
            
            if found:
                # Si trouvé, on lance l'extraction de métadonnées
                meta = self.extract_metadata(response, site_data.get("selectors"))
                
                with self.print_lock:
                    print(f"[+] FOUND: {username} on {site_name:<10} -> {url}")
                    if meta:
                        for k, v in meta.items():
                            print(f"    └── {k}: {v}")
                
                self.results.append({
                    "username": username,
                    "site": site_name, 
                    "url": url, 
                    "metadata": meta
                })
        
        except:
            pass

    def run_dorking(self):
        """Module 3 : Google Dorking"""
        print(f"\n[*] Lancement du module Google Dorking pour '{self.original_username}'...")
        query = f'intext:"{self.original_username}" OR inurl:"{self.original_username}"'
        
        try:
            # Recherche de 5 résultats max pour éviter le ban IP
            for url in search(query, num_results=5):
                with self.print_lock:
                    print(f"[G] Google Hit: {url}")
                self.results.append({"site": "Google Dork", "url": url, "status": "DORKED"})
        except Exception as e:
            print(f"[!] Erreur Google (Rate Limit probable): {e}")

    def run(self):
        print(f"[*] Cible principale : {self.original_username}")
        
        # Lance le scan normal (Multi-threadé)
        threads = []
        for username in self.usernames_to_check:
            for site_name, site_data in self.sites.items():
                t = threading.Thread(target=self.check_site, args=(site_name, site_data, username))
                threads.append(t)
                t.start()
                time.sleep(0.05)

        for t in threads:
            t.join()

    def save_report(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"\n[V] Rapport sauvegardé : {filename}")

# --- CLI ---
if __name__ == "__main__":
    print(BANNER)
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", required=True, help="Pseudo cible")
    parser.add_argument("-p", "--permutations", action="store_true", help="Activer la génération de variantes")
    parser.add_argument("-g", "--google", action="store_true", help="Activer le Google Dorking (Lent)")
    parser.add_argument("-o", "--output", help="Fichier de sortie JSON")
    
    args = parser.parse_args()

    tracker = GhostTracker(args.username, use_permutations=args.permutations)
    tracker.run()
    
    if args.google:
        tracker.run_dorking()

    if args.output:
        tracker.save_report(args.output)