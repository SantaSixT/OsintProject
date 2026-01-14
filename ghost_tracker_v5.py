import requests
from bs4 import BeautifulSoup
import time
import random
import threading
import json
import argparse
import sys
import os
import unidecode # pip install unidecode (Optionnel, pour gérer les accents é -> e)
from googlesearch import search 

# Note le 'r' ici pour corriger le warning
BANNER = r"""
   ________                  __     
  /  _____/  __ __   ______ /  |_   
 /   \  ___ |  |  \ /  ___/|   __\  
 \    \_\  \|  |  / \___ \ |  |     
  \______  /|____/ /____  >|__|     
         \/             \/          
  v5.0 - People Hunter Edition
"""

class GhostTracker:
    def __init__(self, target, mode="username", sites_file="sites.json"):
        self.target = target
        self.mode = mode # 'username' ou 'name'
        self.results = []
        self.print_lock = threading.Lock()
        self.sites = self.load_sites(sites_file)
        self.usernames_to_check = []
        
        # Initialisation selon le mode
        if self.mode == "name":
            self.generate_name_variants()
        else:
            self.usernames_to_check = [target]
            # Si on veut des permutations de pseudo simple, on pourrait l'ajouter ici
            
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def load_sites(self, filepath):
        if not os.path.exists(filepath):
            return {}
        with open(filepath, 'r') as f:
            return json.load(f)

    def generate_name_variants(self):
        """Transforme 'Jean Dupont' en liste de pseudos probables"""
        try:
            # Nettoyage (supprime accents et minuscules)
            # Si unidecode n'est pas installé, on fait un lower() simple
            try:
                clean_name = unidecode.unidecode(self.target).lower()
            except NameError:
                clean_name = self.target.lower()
                
            parts = clean_name.split()
            if len(parts) < 2:
                print("[!] Erreur: Il faut 'Prénom Nom' pour générer des variantes.")
                self.usernames_to_check = [clean_name]
                return

            f = parts[0] # Firstname
            l = parts[1] # Lastname
            
            # La liste magique des formats standards
            variants = [
                f"{f}{l}",       # jeandupont
                f"{f}.{l}",      # jean.dupont
                f"{f}-{l}",      # jean-dupont
                f"{f}_{l}",      # jean_dupont
                f"{l}{f}",       # dupontjean
                f"{l}.{f}",      # dupont.jean
                f"{f}{l}1",      # jeandupont1
                f"{f[0]}{l}",    # jdupont
                f"{f[0]}.{l}"    # j.dupont
            ]
            self.usernames_to_check = list(set(variants))
            print(f"[*] Mode 'People' activé. Variantes générées : {self.usernames_to_check}")
            
        except Exception as e:
            print(f"[!] Erreur génération variantes : {e}")

    def extract_metadata(self, response, selectors):
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = {}
        if not selectors: return None
        
        # ... (Code identique à la v4 pour extraction bio/image) ...
        # Pour raccourcir la réponse ici, je garde la logique existante
        if "bio" in selectors:
            try:
                sel = selectors["bio"]
                if "meta" in sel:
                    tag = soup.select_one(sel)
                    if tag and tag.get("content"): metadata["Bio"] = tag["content"][:80] + "..."
                else:
                    tag = soup.select_one(sel)
                    if tag: metadata["Bio"] = tag.get_text(strip=True)[:80] + "..."
            except: pass
            
        if "image" in selectors:
            try:
                tag = soup.select_one(selectors["image"])
                if tag and tag.get("content"): metadata["Avatar"] = tag["content"]
            except: pass
            
        return metadata

    def check_site(self, site_name, site_data, username):
        url = site_data["url"].format(username)
        try:
            response = requests.get(url, headers=self.headers, timeout=5) # Timeout réduit car beaucoup de variantes
            found = False

            if site_data.get("errorType") == "status_code":
                if response.status_code == 200: found = True
            
            if found:
                meta = self.extract_metadata(response, site_data.get("selectors"))
                with self.print_lock:
                    print(f"[+] FOUND: '{username}' on {site_name:<10} -> {url}")
                    if meta:
                        for k, v in meta.items(): print(f"    └── {k}: {v}")
                
                self.results.append({"query": username, "site": site_name, "url": url, "metadata": meta})
        except: pass

    def run_google_people_search(self):
        """Recherche spécifique pour les Noms Réels (LinkedIn, Facebook...)"""
        print(f"\n[*] Recherche Google ciblée pour l'identité : '{self.target}'...")
        
        # Dorks spécifiques pour les réseaux pro/perso
        dorks = [
            f'site:linkedin.com/in/ "{self.target}"',
            f'site:facebook.com "{self.target}"',
            f'site:instagram.com "{self.target}"',
            f'site:twitter.com "{self.target}"'
        ]
        
        for query in dorks:
            try:
                for url in search(query, num_results=3, lang="fr"):
                    with self.print_lock:
                        print(f"[G] Profil Découvert : {url}")
                    self.results.append({"site": "Google Dork", "url": url, "status": "CONFIRMED_IDENTITY"})
                    time.sleep(1) # Pause anti-ban Google
            except Exception as e:
                print(f"[!] Rate Limit Google atteint sur la requête : {query}")
                break

    def run(self):
        print(f"[*] Cible : {self.target} | Mode : {self.mode.upper()}")
        
        # 1. Scan des comptes (Usernames + Variantes)
        threads = []
        for username in self.usernames_to_check:
            for site_name, site_data in self.sites.items():
                t = threading.Thread(target=self.check_site, args=(site_name, site_data, username))
                threads.append(t)
                t.start()
                time.sleep(0.01) # Très rapide

        for t in threads:
            t.join()
            
        # 2. Si mode Name, on lance le module Google spécialisé
        if self.mode == "name":
            self.run_google_people_search()

    def save_report(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"\n[V] Rapport sauvegardé : {filename}")

if __name__ == "__main__":
    print(BANNER)
    parser = argparse.ArgumentParser()
    
    # Groupe exclusif : Soit on cherche un pseudo, soit un nom
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--username", help="Recherche par pseudo exact")
    group.add_argument("-n", "--name", help="Recherche par Prénom Nom (entre guillemets)")
    
    parser.add_argument("-o", "--output", help="Fichier JSON de sortie")
    
    args = parser.parse_args()

    if args.name:
        # Installation auto si besoin : pip install unidecode
        try:
            import unidecode
        except ImportError:
            print("[Info] Pour une meilleure gestion des accents : pip install unidecode")

        tracker = GhostTracker(args.name, mode="name")
    else:
        tracker = GhostTracker(args.username, mode="username")

    tracker.run()
    
    if args.output:
        tracker.save_report(args.output)