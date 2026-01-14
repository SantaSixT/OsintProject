import unidecode

class EmailGenerator:
    def __init__(self):
        self.domains = [
            "gmail.com", 
            "outlook.com", 
            "hotmail.com", 
            "yahoo.fr", 
            "protonmail.com"
        ]

    def generate(self, raw_input):
        """Génère une liste d'emails potentiels à partir d'un Prénom Nom"""
        emails = []
        
        # Nettoyage
        try:
            clean = unidecode.unidecode(raw_input).lower().strip()
        except:
            return []
            
        parts = clean.split()
        if len(parts) < 2:
            return [] # Il faut Prénom + Nom

        f = parts[0] # Firstname
        l = "".join(parts[1:]) # Lastname (collé si composé)

        # Les formats classiques
        templates = [
            f"{f}.{l}",      # jean.dupont
            f"{f}{l}",       # jeandupont
            f"{f}_{l}",      # jean_dupont
            f"{f[0]}{l}",    # jdupont
            f"{f}.{l[0]}",   # jean.d
            f"{l}.{f}",      # dupont.jean
        ]

        for temp in templates:
            for dom in self.domains:
                emails.append(f"{temp}@{dom}")
        
        return emails