import unidecode

class EmailGenerator:
    def __init__(self):
        # Liste exhaustive des providers
        self.domains = [
            # --- Globaux ---
            "gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com",
            "aol.com", "msn.com", "live.com", "me.com", "yahoo.fr", "hotmail.fr",
            
            # --- France (FAI) ---
            "orange.fr", "wanadoo.fr", "free.fr", "sfr.fr", "laposte.net", 
            "bbox.fr", "neuf.fr", "numericable.fr",
            
            # --- Tech / Privacy ---
            "protonmail.com", "proton.me", "duck.com", "pm.me", "tutanota.com",
            
            # --- Business / Autres ---
            "yandex.com", "mail.ru", "zoho.com", "gmx.com", "mail.com"
        ]

    def generate(self, raw_input):
        """Génère une liste d'emails potentiels à partir d'un Prénom Nom"""
        emails = []
        
        try:
            clean = unidecode.unidecode(raw_input).lower().strip()
        except:
            return []
            
        parts = clean.split()
        if len(parts) < 2:
            return []

        f = parts[0] # Prénom
        l = "".join(parts[1:]) # Nom (collé)
        
        # Variations de format
        templates = [
            f"{f}.{l}",      # jean.dupont
            f"{f}{l}",       # jeandupont
            f"{f}_{l}",      # jean_dupont
            f"{l}.{f}",      # dupont.jean
            f"{f[0]}{l}",    # jdupont
            f"{f}.{l[0]}",   # jean.d (Risqué mais courant)
        ]

        for temp in templates:
            for dom in self.domains:
                emails.append(f"{temp}@{dom}")
        
        return emails