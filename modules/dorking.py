from duckduckgo_search import DDGS
import time
import random

def google_dorking(target_identity, max_results=5):
    """
    Effectue des recherches via DuckDuckGo (plus permissif que Google)
    pour trouver des traces hors réseaux sociaux.
    """
    results = []
    
    # Stratégies de recherche (Dorks) adaptées pour DuckDuckGo
    # Note : DDG supporte très bien site:, filetype:, etc.
    queries = [
        f'site:linkedin.com/in/ "{target_identity}"',
        f'site:twitter.com "{target_identity}"',
        f'"{target_identity}" filetype:pdf',
        f'site:pastebin.com "{target_identity}"',
        f'inurl:"{target_identity.replace(" ", "")}"' # Recherche dans les URL
    ]
    
    print(f"[*] Démarrage Radar (DuckDuckGo) pour : {target_identity}")
    
    # On utilise un gestionnaire de contexte pour DDGS
    with DDGS() as ddgs:
        for query in queries:
            try:
                # DDGS est simple : on itère sur les résultats
                # region="fr-fr" permet de cibler la France
                ddg_gen = ddgs.text(query, region='fr-fr', max_results=max_results)
                
                for r in ddg_gen:
                    title = r.get('title', 'N/A')
                    link = r.get('href', '')
                    snippet = r.get('body', '')

                    # On ajoute au rapport uniquement si on a un lien
                    if link:
                        results.append({
                            "site": "DuckDuckGo", # On note la source
                            "username": query,    # La requête utilisée
                            "url": link,
                            "category": "hors-piste",
                            "metadata": {
                                "Titre": title[:50] + "...", 
                                "Extrait": snippet[:100] + "..."
                            }
                        })
                
                # Petite pause pour être poli (Good OpSec)
                time.sleep(random.uniform(1, 2))
                    
            except Exception as e:
                print(f"[!] Erreur DuckDuckGo sur '{query}': {e}")
                # On continue quand même avec les autres requêtes
                continue
            
    return results