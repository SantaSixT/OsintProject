import streamlit as st
import pandas as pd
import json
import time

# Import des modules internes
from modules.scraper import GhostScraper
from modules.generator import generate_usernames
from modules.dorking import google_dorking 

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="GhostTracker OSINT",
    page_icon="👻",
    layout="wide"
)

# --- CSS CUSTOM (Style Hacker/Dark Mode) ---
st.markdown("""
<style>
    .stButton>button {
        color: white;
        background-color: #ff4b4b;
        border-radius: 5px;
        height: 3em;
        width: 100%;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #ff2b2b;
    }
    .stProgress > div > div > div > div {
        background-color: #00ff00;
    }
    /* Style pour les cartes de résultats */
    .stExpander {
        border: 1px solid #333;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- EN-TÊTE ---
st.title("👻 GhostTracker - OSINT Cockpit")
st.markdown("---")

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.header("🎯 Configuration de la Cible")
    
    # Choix du mode
    target_type = st.radio(
        "Mode de recherche :", 
        ["Pseudo Unique", "Identité (Prénom Nom)"],
        help="Identité va générer des variantes (ex: j.dupont, jeandupont...)"
    )
    
    user_input = st.text_input("Entrée Cible", placeholder="ex: SantaSixT ou Jean Dupont")
    
    st.markdown("### ⚙️ Filtres & Modules")
    use_dorking = st.checkbox("Activer Google Dorking (Lent)", value=False, help="Recherche hors des sites connus via Google (PDF, Pastebin, Blogs...)")
    scan_tech = st.checkbox("Focus Tech", value=True, help="GitHub, DockerHub, GitLab...")
    
    st.markdown("---")
    launch_btn = st.button("🚀 LANCER L'INVESTIGATION")
    st.markdown("*v2.1 - DevSecOps Edition*")

# --- ZONE PRINCIPALE (LOGIQUE) ---
col1, col2 = st.columns([2, 1])

if launch_btn and user_input:
    # 1. INITIALISATION
    scraper = GhostScraper() # Charge la configuration des sites
    final_results = []
    
    with col1:
        st.subheader("📡 Live Feed")
        status_area = st.empty() # Zone de texte dynamique pour les logs
        progress_bar = st.progress(0)
        
        # 2. GÉNÉRATION DES CIBLES (Usernames)
        if target_type == "Identité (Prénom Nom)":
            targets_to_scan = generate_usernames(user_input)
            st.info(f"🧬 Mode Générateur activé : {len(targets_to_scan)} variantes générées (j.dupont, jeandupont...).")
        else:
            targets_to_scan = [user_input]

        # 3. BOUCLE D'INVESTIGATION (OSINT Classique)
        total_steps = len(targets_to_scan)
        current_step = 0
        
        # Fonction callback pour mettre à jour l'UI depuis le scraper
        def update_ui(msg):
            status_area.code(msg)

        # On itère sur chaque variante de pseudo
        for target in targets_to_scan:
            status_area.text(f"🔍 Scan de la variante : {target}...")
            
            # Le scraper stocke les résultats dans sa propre liste interne
            scraper.scan_username(target, callback_status=update_ui)
            
            # Mise à jour de la barre de progression
            current_step += 1
            progress_bar.progress(int((current_step / total_steps) * 100))
        
        # On récupère les résultats du scraper (Partie 1)
        # .copy() est important pour ne pas modifier la liste originale par erreur
        final_results = scraper.results.copy()

        # 4. MODULE GOOGLE DORKING (Radar Hors-Piste)
        if use_dorking:
            st.markdown("---")
            status_area.warning("📡 Lancement du Radar Google (Cela peut prendre du temps)...")
            try:
                # On cherche sur le nom réel saisi par l'utilisateur (plus pertinent que les pseudos)
                dork_results = google_dorking(user_input)
                
                if dork_results:
                    final_results.extend(dork_results)
                    st.success(f"🔎 Google a trouvé {len(dork_results)} traces supplémentaires !")
                else:
                    st.info("Rien trouvé de plus sur Google.")
            except Exception as e:
                st.error(f"Erreur module Dorking : {e}")

        # 5. AFFICHAGE FINAL DES RÉSULTATS (CARTES)
        st.success(f"Investigation terminée ! {len(final_results)} traces trouvées au total.")
        
        if final_results:
            for res in final_results:
                # On détermine l'icône selon la catégorie
                icon = "🌐"
                if res.get('category') == 'coding': icon = "💻"
                elif res.get('category') == 'social': icon = "🗣️"
                elif res.get('category') == 'hors-piste': icon = "🔎"

                # Titre de la carte
                card_title = f"{icon} {res['site']} - {res['username']}"
                
                with st.expander(card_title):
                    st.markdown(f"**Lien:** [{res['url']}]({res['url']})")
                    
                    # Affichage Métadonnées (Bio, Avatar, Info Dorking)
                    if res.get('metadata'):
                        meta = res['metadata']
                        cols = st.columns([1, 3])
                        
                        with cols[0]:
                            if "Avatar" in meta:
                                st.image(meta['Avatar'], width=100)
                            else:
                                st.write("👤 Pas d'avatar")
                                
                        with cols[1]:
                            if "Bio" in meta:
                                st.info(f"**Bio:** {meta['Bio']}")
                            if "Location" in meta:
                                st.write(f"📍 **Lieu:** {meta['Location']}")
                            if "Info" in meta: # Pour les résultats Google
                                st.warning(f"Note: {meta['Info']}")

    # --- COLONNE DE DROITE (RAPPORT & EXPORT) ---
    with col2:
        st.subheader("📊 Rapport Consolidé")
        if final_results:
            # Création du DataFrame pour le tableau
            df = pd.DataFrame(final_results)
            
            # Sélection des colonnes à afficher
            # On vérifie si les colonnes existent pour éviter les erreurs si la liste est vide
            display_cols = [col for col in ['site', 'username', 'category'] if col in df.columns]
            
            st.dataframe(df[display_cols], hide_index=True)
            
            # Bouton Export JSON
            json_results = json.dumps(final_results, indent=4)
            st.download_button(
                label="💾 Télécharger le Rapport JSON",
                data=json_results,
                file_name=f"rapport_{user_input.replace(' ', '_')}.json",
                mime="application/json"
            )
            
            # Statistiques rapides
            st.metric("Total Traces", len(final_results))
            st.metric("Variantes testées", len(targets_to_scan))
            
        else:
            st.info("En attente de résultats...")
            # Petit GIF d'attente stylé
            st.image("https://media.giphy.com/media/l0HlO4p8jVpMQeI3m/giphy.gif", caption="Système prêt...", width=200)

elif launch_btn and not user_input:
    st.error("⚠️ Erreur : Veuillez entrer une cible.")