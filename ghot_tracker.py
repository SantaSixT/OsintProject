import requests
from bs4 import BeautifulSoup
import time
import random
import threading

class OsintTracker:
    def __init__(self, username):
        self.username = username
        self.results = {}
        # Verrou pour éviter que les messages se mélangent dans la console
        self.print_lock = threading.Lock()
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
        ]

        self.targets = {
            "GitHub": {
                "url": "https://github.com/{}",
                "logic": "status_code"
            },
            "Wikipedia": { # Wikipedia User Page
                "url": "https://en.wikipedia.org/wiki/User:{}",
                "logic": "status_code"
            },
            "Reddit": {
                "url": "https://www.reddit.com/user/{}",
                "logic": "status_code"
            },
            "Medium": {
                "url": "https://medium.com/@{}",
                "logic": "status_code"
            },
             "Pastebin": {
                "url": "https://pastebin.com/u/{}",
                "logic": "status_code"
            },
             "DockerHub": {
                "url": "https://hub.docker.com/u/{}",
                "logic": "status_code"
            }
        }

    def get_stealth_headers(self):
        """Retourne des headers HTTP complets pour contourner les WAF basiques"""
        ua = random.choice(self.user_agents)
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.google.com/", # On fait croire qu'on vient de Google
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }

    def check_site(self, site, data):
        url = data["url"].format(self.username)
        headers = self.get_stealth_headers()
        
        try:
            # Timeout augmenté à 10s
            response = requests.get(url, headers=headers, timeout=10)
            
            exists = False
            
            if data["logic"] == "status_code":
                if response.status_code == 200:
                    exists = True
                elif response.status_code == 404:
                    exists = False
                elif response.status_code == 403:
                    with self.print_lock:
                        print(f"[!] {site} : Bloqué (403 WAF/Anti-Bot) - Essai manuel recommandé")
                    return
                else:
                    return

            if exists and "check_text" in data:
                soup = BeautifulSoup(response.text, 'html.parser')
                if data["check_text"] in soup.get_text():
                    exists = False 

            if exists:
                info = self.extract_details(response)
                # Utilisation du Lock pour un affichage propre
                with self.print_lock:
                    print(f"[+] TROUVÉ : {site} -> {url}")
                    if info:
                        print(f"    └── Info: {info}")
                    self.results[site] = url

        except requests.exceptions.Timeout:
            with self.print_lock:
                print(f"[!] {site} : Timeout (Trop lent)")
        except requests.exceptions.RequestException as e:
            pass # On ignore les autres erreurs pour garder la sortie propre

    def extract_details(self, response):
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else ""
            # Nettoyage basique du titre (supprime les retours à la ligne)
            return " ".join(title.split())[:60] + "..."
        except:
            return None

    def run(self):
        print(f"--- Démarrage du scan OSINT (Stealth Mode) pour : {self.username} ---")
        
        threads = []
        for site, data in self.targets.items():
            t = threading.Thread(target=self.check_site, args=(site, data))
            threads.append(t)
            t.start()
            time.sleep(random.uniform(0.2, 0.6)) # Pause un peu plus longue

        for t in threads:
            t.join()
            
        print(f"\n--- Scan terminé. {len(self.results)} profils trouvés. ---")

if __name__ == "__main__":
    target_pseudo = input("Entrez le pseudo à traquer : ")
    tracker = OsintTracker(target_pseudo)
    tracker.run()