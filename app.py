import streamlit as st
import pandas as pd
import json
import time

# --- IMPORTS DES MODULES INTERNES ---
from modules.scraper import GhostScraper
from modules.generator import generate_usernames
from modules.dorking import google_dorking 
from modules.email_utils import EmailGenerator # <--- NOUVEAU MODULE
from modules.mapping import generate_map 
from modules.secrets import SecretHunter 
from streamlit_folium import st_folium    

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="GhostTracker V3",
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
    scan_tech = st.checkbox("🔍 Scan Comptes (Social/Tech)", value=True, help="GitHub, DockerHub, GitLab...")
    use_dorking = st.checkbox("📡 Radar Hors-Piste (Dorking)", value=False, help="Recherche Google/DDG (PDF, Pastebin...)")
    scan_email = st.checkbox("📧 Scan Emails Probables", value=False, help="Génère et cherche des emails (Gmail/Outlook...)")
    
    st.markdown("---")
    launch_btn = st.button("🚀 LANCER L'INVESTIGATION")
    st.markdown("*v3.0 - Full Spectrum Edition*")

# --- ZONE PRINCIPALE (LOGIQUE) ---
col1, col2 = st.columns([2, 1])

if launch_btn and user_input:
    # 1. INITIALISATION
    scraper = GhostScraper() 
    email_gen = EmailGenerator() # <--- INIT EMAIL GEN
    final_results = []
    
    with col1:
        st.subheader("📡 Live Feed")
        status_area = st.empty() 
        progress_bar = st.progress(0)
        
        # 2. GÉNÉRATION DES CIBLES (USERNAMES)
        if target_type == "Identité (Prénom Nom)":
            targets_to_scan = generate_usernames(user_input)
            st.info(f"🧬 Mode Générateur activé : {len(targets_to_scan)} variantes générées.")
        else:
            targets_to_scan = [user_input]

        # 3. BOUCLE D'INVESTIGATION (SCAN COMPTES)
        if scan_tech:
            total_steps = len(targets_to_scan)
            current_step = 0
            step_size = 1.0 / total_steps if total_steps > 0 else 1

            def update_ui(msg):
                status_area.code(msg)

            for target in targets_to_scan:
                status_area.text(f"🔍 Scan de la variante : {target}...")
                scraper.scan_username(target, callback_status=update_ui)
                
                current_step += 1
                progress_bar.progress(min(current_step / total_steps, 1.0))
            
            final_results.extend(scraper.results)

        # 4. MODULE RADAR HORS-PISTE (DORKING CLASSIQUE)
        if use_dorking:
            st.markdown("---")
            status_area.warning("📡 Lancement du Radar (OpSec: Délai actif)...")
            try:
                # email_mode=False car on cherche la personne, pas ses mails
                dork_results = google_dorking(user_input, email_mode=False)
                
                if dork_results:
                    final_results.extend(dork_results)
                    st.success(f"🔎 Radar a trouvé {len(dork_results)} traces supplémentaires !")
                else:
                    st.info("Rien trouvé de plus sur les moteurs de recherche.")
            except Exception as e:
                st.error(f"Erreur module Dorking : {e}")

        # 5. MODULE EMAIL (NOUVEAU)
        if scan_email and target_type == "Identité (Prénom Nom)":
            st.markdown("---")
            status_area.warning("📧 Génération & Test des Emails...")
            
            # A. On génère les mails
            generated_emails = email_gen.generate(user_input)
            if generated_emails:
                st.caption(f"Test de {len(generated_emails)} combinaisons (Gmail, Outlook, Yahoo...)")
                
                # B. On Dork ces emails (Est-ce qu'ils apparaissent sur Pastebin, LinkedIn, etc ?)
                # Attention : On en prend max 5 pour pas se faire ban par DuckDuckGo
                subset_emails = generated_emails[:5] 
                
                email_hits = google_dorking(subset_emails, email_mode=True)
                
                if email_hits:
                    final_results.extend(email_hits)
                    st.error(f"⚠️ {len(email_hits)} emails potentiels trouvés sur le web !")
                else:
                    st.info("Aucune trace publique de ces emails (C'est bon signe).")
            else:
                st.warning("Impossible de générer des emails (Il faut Prénom + Nom).")

        # 6. AFFICHAGE FINAL DES RÉSULTATS (CARTES)
        st.success(f"Investigation terminée ! {len(final_results)} traces trouvées au total.")
        
        if final_results:
            # Affichage des cartes textuelles
            for res in final_results:
                icon = "🌐"
                if res.get('category') == 'coding': icon = "💻"
                elif res.get('category') == 'social': icon = "🗣️"
                elif res.get('category') == 'hors-piste': icon = "🔎"
                elif res.get('category') == 'mail-leak': icon = "📧"

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

            # 7. MODULE CARTOGRAPHIE
            st.markdown("---")
            st.subheader("🌍 Géolocalisation des Cibles")
            
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

        # 8. MODULE SECRET HUNTER (RED TEAM)
        st.markdown("---")
        st.subheader("⚔️ Analyse de Vulnérabilité (Secret Hunter)")
        
        if scan_tech: 
            with st.spinner("Analyse heuristique des données récupérées..."):
                hunter = SecretHunter()
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
            
            display_cols = [col for col in ['site', 'username', 'category'] if col in df.columns]
            st.dataframe(df[display_cols], hide_index=True)
            
            json_results = json.dumps(final_results, indent=4)
            st.download_button(
                label="💾 Télécharger JSON",
                data=json_results,
                file_name=f"rapport_{user_input.replace(' ', '_')}.json",
                mime="application/json"
            )
            
            st.metric("Total Traces", len(final_results))
            st.metric("Variantes testées", len(targets_to_scan))
            
        else:
            st.info("En attente de résultats...")
            st.image("https://media.giphy.com/media/l0HlO4p8jVpMQeI3m/giphy.gif", caption="Système prêt...", width=200)

elif launch_btn and not user_input:
    st.error("⚠️ Erreur : Veuillez entrer une cible.")