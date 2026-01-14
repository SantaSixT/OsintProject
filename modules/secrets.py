import re

class SecretHunter:
    def __init__(self):
        # Dictionnaire des signatures (Regex)
        # C'est ici qu'on définit ce qu'est un "secret"
        self.signatures = {
            "AWS API Key": r"AKIA[0-9A-Z]{16}",
            "Generic API Key": r"(api_key|apikey|access_token)[\s:=]+([a-zA-Z0-9\-_]{20,})",
            "Google API Key": r"AIza[0-9A-Za-z\\-_]{35}",
            "Private Key Block": r"-----BEGIN (RSA|DSA|EC|PGP) PRIVATE KEY-----",
            "Password Assignment": r"(password|passwd|pwd|secret)[\s:=]+[\'\"]([^\'\"]+)[\'\"]",
            "Email Pro": r"[a-zA-Z0-9._%+-]+@(?!gmail|yahoo|hotmail|outlook)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" # Emails non-grand public
        }

    def scan_text(self, text, source_url):
        """
        Scanne un texte brut pour trouver des patterns suspects.
        Retourne une liste d'alertes.
        """
        findings = []
        if not text:
            return findings

        for risk_name, regex in self.signatures.items():
            # Recherche des patterns
            matches = re.finditer(regex, text, re.IGNORECASE)
            for match in matches:
                # On récupère ce qu'on a trouvé
                captured = match.group(0)
                
                # Pour la sécurité (affichage), on censure partiellement le secret
                if len(captured) > 10:
                    masked = captured[:4] + "*" * (len(captured)-8) + captured[-4:]
                else:
                    masked = "***"

                findings.append({
                    "type": risk_name,
                    "preview": masked, # On ne stocke pas le secret en clair dans le rapport final (Bonne pratique)
                    "source": source_url,
                    "raw_match": captured # (Optionnel: à garder uniquement si besoin de debug)
                })
                
        return findings

    def analyze_results(self, final_results):
        """
        Parcours tous les résultats du scan OSINT et cherche des secrets
        dans les métadonnées (Bios, Snippets Dorking, etc.)
        """
        all_findings = []
        
        print("[*] Démarrage du Secret Hunter (Analyse Heuristique)...")
        
        for res in final_results:
            # On construit un gros bloc de texte avec tout ce qu'on sait sur ce résultat
            content_to_scan = ""
            
            # 1. On scanne l'URL (parfois le token est dans l'URL)
            content_to_scan += f" {res.get('url', '')} "
            
            # 2. On scanne les métadonnées (Bio, Extraits Google...)
            meta = res.get('metadata', {})
            for key, value in meta.items():
                content_to_scan += f" {value} "

            # Analyse
            leaks = self.scan_text(content_to_scan, res['url'])
            if leaks:
                all_findings.extend(leaks)
                
        return all_findings