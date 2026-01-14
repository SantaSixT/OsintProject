import unidecode

def generate_usernames(input_name):
    """
    Transforme 'Jean Dupont' en liste de pseudos probables :
    ['jeandupont', 'j.dupont', 'dupont_jean', etc.]
    """
    # 1. Nettoyage (Accents et minuscules)
    try:
        clean_name = unidecode.unidecode(input_name).lower()
    except:
        clean_name = input_name.lower()
    
    parts = clean_name.split()
    
    # Si l'utilisateur n'a mis qu'un mot (ex: "SantaSixT"), on le renvoie tel quel
    if len(parts) < 2:
        return [clean_name]

    f = parts[0] # Firstname (Prénom)
    l = parts[1] # Lastname (Nom)
    
    # 2. La liste des variantes standards
    variants = [
        f"{f}{l}",       # jeandupont
        f"{f}.{l}",      # jean.dupont
        f"{f}-{l}",      # jean-dupont
        f"{f}_{l}",      # jean_dupont
        f"{l}{f}",       # dupontjean
        f"{l}.{f}",      # dupont.jean
        f"{l}_{f}",      # dupont_jean
        f"{f[0]}{l}",    # jdupont
        f"{f[0]}.{l}",   # j.dupont
        f"{f}{l[0]}"     # jeand
    ]
    
    # On dédoublonne la liste au cas où
    return list(set(variants))