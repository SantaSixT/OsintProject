from duckduckgo_search import DDGS
import time
import random
import unidecode

BLACKLIST_DOMAINS = [
    "microsoft.com", "office.com", "wikipedia.org", 
    "baidu.com", "zhihu.com", "adobe.com", "amazon.com"
]

def normalize(text):
    if not text: return ""
    return unidecode.unidecode(text).lower()

def google_dorking(target_identity, email_mode=False):
    """
    Si email_mode=True, target_identity est une liste d'emails à vérifier.
    Sinon, c'est le nom de la personne.
    """
    results = []
    queries = []

    # --- MODE 1 : RECHERCHE DE MAILS (Nouveau !) ---
    if email_mode:
        # On cherche si ces emails apparaissent dans des leaks ou des profils
        # target_identity est ici une liste d'emails
        for email in target_identity:
            queries.append(f'"{email}"') # Recherche exacte de l'email
            queries.append(f'site:pastebin.com "{email}"') # Recherche dans les leaks
        
        print(f"[*] Démarrage Radar Email pour {len(target_identity)} adresses...")

    # --- MODE 2 : RECHERCHE DE PERSONNE (Classique) ---
    else:
        target_identity = target_identity.strip()
        social_sites = ["linkedin.com/in", "facebook.com", "twitter.com", "instagram.com", "tiktok.com"]
        for site in social_sites:
            queries.append(f'site:{site} "{target_identity}"')
        
        queries.append(f'"{target_identity}"') # Recherche large
        queries.append(f'"{target_identity}" filetype:pdf') # Docs
        
        print(f"[*] Démarrage Radar Identité pour : '{target_identity}'")

    try:
        with DDGS() as ddgs:
            for query in queries:
                try:
                    # Max 3 résultats pour aller vite
                    ddg_gen = ddgs.text(query, region='fr-fr', max_results=3)
                    
                    if not ddg_gen: continue

                    for r in ddg_gen:
                        link = r.get('href', '')
                        title = r.get('title', 'N/A')
                        snippet = r.get('body', '')

                        # 1. FILTRE ANTI-SPAM (Blacklist)
                        if any(blocked in link for blocked in BLACKLIST_DOMAINS):
                            continue

                        # 2. FILTRE DE PERTINENCE (Seulement pour les noms, pas les emails)
                        if not email_mode:
                            flat_target = normalize(target_identity)
                            flat_content = normalize(title + " " + snippet + " " + link)
                            parts = flat_target.split()
                            
                            # Si on a "Prénom Nom"
                            if len(parts) >= 2:
                                lastname = parts[-1]
                                firstname = parts[0]
                                # On exige le NOM DE FAMILLE + (Prénom OU Initiale)
                                # Ex: "Rohrbasser" ET ("Antoine" OU "A")
                                condition_nom = lastname in flat_content
                                condition_prenom = (firstname in flat_content) or (f" {firstname[0]} " in flat_content)
                                
                                if not (condition_nom and condition_prenom):
                                    continue
                            elif flat_target not in flat_content:
                                continue

                        # Si on arrive ici, c'est validé !
                        cat = "mail-leak" if email_mode else "hors-piste"
                        if "linkedin" in link: cat = "social"
                        
                        results.append({
                            "site": "DuckDuckGo",
                            "username": query.replace('"', '').replace('site:pastebin.com ', ''),
                            "url": link,
                            "category": cat,
                            "metadata": {
                                "Info": "Trouvé via Radar",
                                "Titre": title[:80],
                                "Extrait": snippet[:100] + "..."
                            }
                        })
                    
                    time.sleep(random.uniform(0.5, 1.0))

                except Exception: continue

    except Exception as e:
        print(f"[!] Erreur DDGS : {e}")
        return []
            
    return results