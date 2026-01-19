from duckduckgo_search import DDGS
import time
import random
import unidecode

# Liste noire des domaines "bruit de fond"
BLACKLIST_DOMAINS = [
    "microsoft.com", "office.com", "wikipedia.org", 
    "baidu.com", "zhihu.com", "adobe.com", "amazon.com",
    "google.com", "apple.com", "facebook.com/help", 
    "support.google.com", "answers.microsoft.com"
]

def normalize(text):
    if not text: return ""
    return unidecode.unidecode(text).lower()

def google_dorking(target_identity, email_mode=False):
    """
    email_mode=True : Active le mode 'Pwned' (recherche de fuites)
    email_mode=False : Recherche de profils classiques
    """
    results = []
    queries = []

    # --- MODE PWNED (Fuites d'emails) ---
    if email_mode:
        # target_identity est ici une liste d'emails générés
        print(f"[*] Démarrage Check 'Pwned' pour {len(target_identity)} adresses...")
        
        # Pour éviter de spammer DDG, on ne teste que les 10 plus probables
        priority_emails = [e for e in target_identity if "gmail" in e or "outlook" in e or "orange" in e or "yahoo" in e]
        # On complète si besoin jusqu'à 8 emails max pour le scan
        scan_list = priority_emails[:8]
        if len(scan_list) < 8:
            scan_list.extend(target_identity[:8-len(scan_list)])
            
        for email in list(set(scan_list)):
            # 1. Recherche brute de l'email
            queries.append(f'"{email}"') 
            
            # 2. Recherche spécifique "Leak" (Fichiers textes, Pastebin...)
            queries.append(f'"{email}" AND (password OR passwd OR dump OR leak)')
            queries.append(f'site:pastebin.com "{email}"')
            queries.append(f'ext:txt "{email}"')

    # --- MODE CLASSIQUE (Profils) ---
    else:
        target_identity = target_identity.strip()
        print(f"[*] Démarrage Radar Identité pour : '{target_identity}'")
        
        social_sites = ["linkedin.com/in", "facebook.com", "twitter.com", "instagram.com", "tiktok.com", "youtube.com"]
        for site in social_sites:
            queries.append(f'site:{site} "{target_identity}"')
        
        queries.append(f'"{target_identity}"')
        queries.append(f'"{target_identity}" filetype:pdf')

    try:
        with DDGS() as ddgs:
            for query in queries:
                try:
                    # On lance la recherche
                    ddg_gen = ddgs.text(query, region='fr-fr', max_results=2)
                    
                    if not ddg_gen: continue

                    for r in ddg_gen:
                        link = r.get('href', '')
                        title = r.get('title', 'N/A')
                        snippet = r.get('body', '')

                        # --- FILTRE 1 : BLACKLIST ---
                        if any(blocked in link for blocked in BLACKLIST_DOMAINS): continue

                        # Normalisation pour l'analyse
                        flat_content = normalize(title + " " + snippet + " " + link)

                        # --- FILTRE 2 : VERIFICATION DE PERTINENCE ---
                        
                        # Cas A : Recherche d'Email (Mode Pwned)
                        if email_mode:
                            # On récupère l'email cherché depuis la requête (entre guillemets)
                            # ex: query = '"jean.dupont@gmail.com" AND password' -> on veut jean.dupont@gmail.com
                            target_email = ""
                            if '"' in query:
                                target_email = normalize(query.split('"')[1])
                            
                            # CORRECTIF : Si l'email n'apparaît pas CLAIREMENT dans le titre ou l'extrait, on jette.
                            # Cela élimine les pages d'aide Facebook ou les forums génériques.
                            if target_email and target_email not in flat_content:
                                continue

                        # Cas B : Recherche d'Identité (Mode Classique)
                        else:
                            flat_target = normalize(target_identity)
                            parts = flat_target.split()
                            
                            if len(parts) >= 2:
                                # Vérif nom de famille obligatoire + prénom/initiale
                                if parts[-1] not in flat_content: continue
                            elif flat_target not in flat_content:
                                continue

                        # --- CLASSIFICATION ---
                        cat = "hors-piste"
                        if email_mode:
                            cat = "mail-leak"
                            # Si on voit "password" dans l'extrait, c'est critique
                            if "password" in snippet.lower() or "leak" in snippet.lower() or "db" in snippet.lower():
                                cat = "CRITICAL_LEAK"
                        elif "linkedin" in link or "facebook" in link or "twitter" in link:
                            cat = "social"

                        results.append({
                            "site": "DuckDuckGo",
                            "username": query.replace('"', '').replace('site:pastebin.com ', ''),
                            "url": link,
                            "category": cat,
                            "metadata": {
                                "Info": "⚠️ Trace de fuite" if cat == "CRITICAL_LEAK" else "Radar Web",
                                "Titre": title[:80],
                                "Extrait": snippet[:100] + "..."
                            }
                        })
                    
                    time.sleep(random.uniform(0.5, 1.2))

                except Exception: continue

    except Exception as e:
        print(f"[!] Erreur DDGS : {e}")
        return []
            
    return results