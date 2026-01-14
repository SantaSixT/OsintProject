import streamlit as st
import pandas as pd
import json
import time

# --- IMPORTS DES MODULES INTERNES ---
from modules.scraper import GhostScraper
from modules.generator import generate_usernames
from modules.dorking import google_dorking 
# [ZONE D'EXTENSION] : Si tu ajoutes des modules d'analyse d'image ou de password breach, import-les ici.
from modules.mapping import generate_map 
from modules.secrets import SecretHunter 
from streamlit_folium import st_folium    

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
    use_dorking = st.checkbox("Activer Radar Hors-Piste (Dorks)", value=False, help="Recherche Google/DDG (PDF, Pastebin...)")
    scan_tech = st.checkbox("Focus Tech", value=True, help="GitHub, DockerHub, GitLab...")
    
    # [ZONE D'EXTENSION] : Ajouter ici un champ pour une Clé API (ex: HaveIBeenPwned)
    # api_key = st.text_input("Clé API HaveIBeenPwned (Optionnel)", type="password")

    st.markdown("---")
    launch_btn = st.button("🚀 LANCER L'INVESTIGATION")
    st.markdown("*v2.2 - Geo-Tactical Edition*")

# --- ZONE PRINCIPALE (LOGIQUE) ---
col1, col2 = st.columns([2, 1])

if launch_btn and user_input:
    # 1. INITIALISATION
    scraper = GhostScraper() 
    final_results = []
    
    with col1:
        st.subheader("📡 Live Feed")
        status_area = st.empty() 
        progress_bar = st.progress(0)
        
        # 2. GÉNÉRATION DES CIBLES
        if target_type == "Identité (Prénom Nom)":
            targets_to_scan = generate_usernames(user_input)
            st.info(f"🧬 Mode Générateur activé : {len(targets_to_scan)} variantes générées.")
        else:
            targets_to_scan = [user_input]

        # 3. BOUCLE D'INVESTIGATION (OSINT CLASSIQUE)
        total_steps = len(targets_to_scan)
        current_step = 0
        
        def update_ui(msg):
            status_area.code(msg)

        for target in targets_to_scan:
            status_area.text(f"🔍 Scan de la variante : {target}...")
            # Le scraper remplit sa liste interne self.results
            scraper.scan_username(target, callback_status=update_ui)
            
            current_step += 1
            progress_bar.progress(int((current_step / total_steps) * 100))
        
        # On récupère les résultats de base
        final_results = scraper.results.copy()

        # 4. MODULE RADAR HORS-PISTE (DORKING)
        if use_dorking:
            st.markdown("---")
            status_area.warning("📡 Lancement du Radar (OpSec: Délai actif)...")
            try:
                # [ZONE D'EXTENSION] : Tu pourrais ajouter ici un sélecteur pour choisir entre Google et DuckDuckGo
                dork_results = google_dorking(user_input)
                
                if dork_results:
                    final_results.extend(dork_results)
                    st.success(f"🔎 Radar a trouvé {len(dork_results)} traces supplémentaires !")
                else:
                    st.info("Rien trouvé de plus sur les moteurs de recherche.")
            except Exception as e:
                st.error(f"Erreur module Dorking : {e}")

        # [ZONE D'EXTENSION] : C'est ici qu'on placera le module "Breach Check" (Vérification de fuites de mots de passe)
        # if check_breach:
        #     breach_results = check_pwned(user_input)
        #     final_results.extend(breach_results)

        # 5. AFFICHAGE FINAL DES RÉSULTATS (CARTES)
        st.success(f"Investigation terminée ! {len(final_results)} traces trouvées au total.")
        
        if final_results:
            # Affichage des cartes textuelles
            for res in final_results:
                icon = "🌐"
                if res.get('category') == 'coding': icon = "💻"
                elif res.get('category') == 'social': icon = "🗣️"
                elif res.get('category') == 'hors-piste': icon = "🔎"

                card_title = f"{icon} {res['site']} - {res['username']}"
                
                with st.expander(card_title):
                    st.markdown(f"**Lien:** [{res['url']}]({res['url']})")
                    
                    if res.get('metadata'):
                        meta = res['metadata']
                        cols = st.columns([1, 3])
                        with cols[0]:
                            if "Avatar" in meta:
                                st.image(meta['Avatar'], width=100)
                            else:
                                st.write("👤 N/A")
                        with cols[1]:
                            if "Bio" in meta: st.info(f"**Bio:** {meta['Bio']}")
                            if "Location" in meta: st.write(f"📍 **Lieu:** {meta['Location']}")
                            if "Info" in meta: st.warning(f"Note: {meta['Info']}")

            # 6. MODULE CARTOGRAPHIE (NOUVEAU)
            st.markdown("---")
            st.subheader("🌍 Géolocalisation des Cibles")
            
            # Vérification rapide avant de lancer le moteur carto
            has_location = any("Location" in r.get('metadata', {}) for r in final_results)
            
            if has_location:
                with st.spinner("Triangulation des positions géographiques..."):
                    map_obj, count = generate_map(final_results)
                    
                    if count > 0:
                        st_folium(map_obj, width=700, height=400)
                        st.caption(f"📍 {count} points identifiés.")
                    else:
                        st.warning("Lieux trouvés, mais géocodage impossible (API Timeout ?).")
            else:
                st.info("Pas de données géographiques dans les profils trouvés.")
# ... (Après la carte géographique) ...

        # --- MODULE 6 : SECRET HUNTER (RED TEAM) ---
        st.markdown("---")
        st.subheader("⚔️ Analyse de Vulnérabilité (Secret Hunter)")
        
        # On peut mettre ça derrière un expander ou un bouton pour ne pas faire peur
        if scan_tech: # Si l'utilisateur a coché "Focus Tech"
            with st.spinner("Analyse heuristique des données récupérées..."):
                hunter = SecretHunter()
                # On scanne TOUT ce qu'on a trouvé (Bio, Dorks, URLs...)
                leaks = hunter.analyze_results(final_results)
                
                if leaks:
                    st.error(f"⚠️ ALERTE : {len(leaks)} secrets potentiels détectés !")
                    
                    for leak in leaks:
                        st.markdown(f"""
                        **Type:** `{leak['type']}`  
                        **Source:** {leak['source']}  
                        **Preuve:** `{leak['preview']}`
                        """)
                else:
                    st.success("🛡️ Aucun secret évident détecté dans les données publiques (Bio/Snippets).")

    # --- COLONNE DE DROITE (RAPPORT & EXPORT) ---
    with col2:
        st.subheader("📊 Rapport Consolidé")
        if final_results:
            df = pd.DataFrame(final_results)
            
            # [ZONE D'EXTENSION] : Ici, tu pourrais ajouter des graphiques (ex: Camembert des catégories)
            # st.bar_chart(df['category'].value_counts())

            display_cols = [col for col in ['site', 'username', 'category'] if col in df.columns]
            st.dataframe(df[display_cols], hide_index=True)
            
            json_results = json.dumps(final_results, indent=4)
            st.download_button(
                label="💾 Télécharger JSON",
                data=json_results,
                file_name=f"rapport_{user_input.replace(' ', '_')}.json",
                mime="application/json"
            )
            
            # [ZONE D'EXTENSION] : Ajouter un bouton pour exporter en PDF ou HTML stylisé
            
            st.metric("Total Traces", len(final_results))
            st.metric("Variantes testées", len(targets_to_scan))
            
        else:
            st.info("En attente de résultats...")
            st.image("https://media.giphy.com/media/l0HlO4p8jVpMQeI3m/giphy.gif", caption="Système prêt...", width=200)

elif launch_btn and not user_input:
    st.error("⚠️ Erreur : Veuillez entrer une cible.")