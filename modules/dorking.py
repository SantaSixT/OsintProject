from googlesearch import search
import time
import random

def google_dorking(target_identity, max_results=5):
    """
    Effectue des recherches Google avancées pour trouver des traces hors réseaux sociaux.
    """
    results = []
    
    # Stratégies de recherche (Dorks)
    queries = [
        # Recherche exacte du nom sur le web
        f'"{target_identity}"',
        
        # Recherche de fichiers PDF/DOC oubliés (CV, Documents)
        f'"{target_identity}" filetype:pdf OR filetype:docx',
        
        # Recherche dans les URL (blogs perso, sous-domaines)
        f'inurl:"{target_identity.replace(" ", "")}"',
        
        # Recherche de mentions sur des sites de paste (fuites de données)
        f'site:pastebin.com "{target_identity}"'
    ]
    
    print(f"[*] Démarrage Google Dorking pour : {target_identity}")
    
    for query in queries:
        try:
            # On demande à Google
            # pause=2.0 est vital pour ne pas se faire bannir l'IP par Google (429 Too Many Requests)
            for url in search(query, num_results=max_results, lang="fr", sleep_interval=2):
                results.append({
                    "site": "Google Dork",
                    "username": query, # On stocke la requête qui a fonctionné
                    "url": url,
                    "category": "hors-piste",
                    "metadata": {"Info": "Trouvé via Google Search"}
                })
                # Petite pause aléatoire supplémentaire par sécurité
                time.sleep(random.uniform(1, 3))
                
        except Exception as e:
            # Si Google bloque (Rate Limit), on arrête ce module mais on ne plante pas l'app
            print(f"[!] Erreur Google : {e}")
            break
            
    return results