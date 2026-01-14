import unidecode
import re

class TargetExpander:
    def __init__(self, raw_input):
        self.raw_input = raw_input
        # Les séparateurs les plus courants sur le web (point, underscore, tiret, rien)
        self.separators = ['.', '_', '-', ''] 
        
    def _clean(self, text):
        """Nettoie : enlève les accents, met en minuscule, garde les tirets pour les noms composés"""
        try:
            # On garde les caractères alphanumériques et les tirets/espaces
            text = unidecode.unidecode(text).lower()
            return text.strip()
        except:
            return text.lower().strip()

    def _generate_variations(self, firstname, lastname):
        """Cœur du moteur de permutation"""
        variations = set()
        
        f = firstname
        l = lastname
        
        # Gestion des noms composés (ex: Jean-Pierre -> jeanpierre)
        f_flat = f.replace("-", "")
        l_flat = l.replace("-", "")
        
        # --- 1. LES CLASSIQUES (Pertinence : ÉLEVÉE) ---
        # jean.dupont, jean_dupont, jeandupont
        for sep in self.separators:
            variations.add(f"{f}{sep}{l}")
            variations.add(f"{l}{sep}{f}")
            
            # Si nom composé, on teste aussi la version collée (jeanpierre.dupont)
            if "-" in f:
                variations.add(f"{f_flat}{sep}{l}")

        # --- 2. LES INITIALES (Pertinence : MOYENNE/ÉLEVÉE) ---
        # j.dupont, dupont.j
        if len(f) > 1:
            f_init = f[0]
            for sep in self.separators:
                variations.add(f"{f_init}{sep}{l}")  # j.dupont
                variations.add(f"{l}{sep}{f_init}")  # dupont.j

        # --- 3. L'ABRÉVIATION INVERSÉE (Pertinence : MOYENNE) ---
        # jean.d (Souvent utilisé sur les outils pro comme Slack/Jira)
        if len(l) > 1:
            l_init = l[0]
            for sep in ['.', '_']: # Rarement utilisé avec des tirets
                variations.add(f"{f}{sep}{l_init}") # jean.d

        # --- 4. LA TRONCATURE / SURNOMS (Pertinence : MOYENNE) ---
        # Christopher -> Chris.Dupont
        if len(f) >= 6: # On ne tronque que les prénoms longs
            f_short = f[:4] # 4 premières lettres
            for sep in self.separators:
                variations.add(f"{f_short}{sep}{l}")
                variations.add(f"{l}{sep}{f_short}")

        return list(variations)

    def expand(self):
        clean_input = self._clean(self.raw_input)
        
        # Détection automatique : Est-ce un "Prénom Nom" ou un "Pseudo" ?
        # On découpe sur les espaces
        parts = clean_input.split()
        
        candidates = []

        # CAS A : Identité Complète détectée (Au moins 2 mots)
        if len(parts) >= 2:
            firstname = parts[0]
            lastname = " ".join(parts[1:]) # Gère "Jean De La Fontaine" -> Lastname = "de la fontaine"
            
            # Nettoyage interne (supprime les espaces dans le nom de famille pour les URL)
            lastname = lastname.replace(" ", "")
            
            candidates = self._generate_variations(firstname, lastname)

        # CAS B : Pseudo unique ou Nom seul
        else:
            # Si l'utilisateur tape juste "dupont" ou "santasixt", on le garde tel quel
            # On ajoute juste quelques variantes techniques basiques
            base = parts[0]
            candidates = [base]
            if len(base) > 4: # On évite de polluer les mots courts
                candidates.append(f"{base}1")
                candidates.append(f"{base}123")
                candidates.append(f"{base}_dev")

        # --- FILTRE DE PERTINENCE FINAL (Anti-Bruit) ---
        final_list = []
        for c in candidates:
            # Règle 1 : Pas de pseudos trop courts (Source de faux positifs énormes)
            # Sauf si l'input de base était court (ex: "Li Wu")
            if len(c) < 5 and len(clean_input) > 4:
                continue
            
            final_list.append(c)

        return sorted(list(set(final_list)))

# Wrapper de compatibilité pour app.py
def generate_usernames(user_input):
    engine = TargetExpander(user_input)
    return engine.expand()