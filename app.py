import streamlit as st
import pandas as pd
import json
import re

# --- IMPORTS DES MODULES INTERNES ---
from modules.scraper import GhostScraper
from modules.generator import generate_usernames
from modules.dorking import google_dorking
from modules.email_utils import EmailGenerator
from modules.mapping import generate_map
from modules.secrets import SecretHunter
from streamlit_folium import st_folium
from modules.report import generate_pdf
from modules.graph import generate_graph
from modules.html_report import generate_html
from modules.image_spy import get_exif_data

# --- IMPORT SECURISE : VISION (RECONNAISSANCE FACIALE) ---
# Si dlib/face_recognition n'est pas installé, l'appli ne plantera pas.
VISION_AVAILABLE = False
try:
    from modules.vision import FaceHunter
    VISION_AVAILABLE = True
except ImportError:
    pass

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="GhostTracker V6", page_icon="👁️", layout="wide")

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .stButton>button { color: white; background-color: #ff4b4b; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #ff2b2b; }
    .match-success { border: 2px solid #00ff00; padding: 10px; border-radius: 5px; background: rgba(0,255,0,0.1); }
    .match-fail { border: 2px solid #ff0000; padding: 10px; border-radius: 5px; background: rgba(255,0,0,0.1); }
    .stProgress > div > div > div > div { background-color: #00ff00; }
    .stExpander { border: 1px solid #333; border-radius: 5px; }
    .debug-text { color: #aaaaaa; font-size: 0.8em; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

st.title("👁️ GhostTracker - Intelligence & Vision")
st.markdown("---")

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.header("🎯 Cible")
    
    # 1. MODULE VISION (UPLOAD)
    uploaded_file = None
    if VISION_AVAILABLE:
        st.subheader("📸 Reconnaissance Faciale")
        uploaded_file = st.file_uploader("Charger photo cible", type=['jpg', 'png', 'jpeg'])
        if not uploaded_file:
            st.info("Chargez une photo pour activer le Face Matcher.")
    else:
        st.warning("⚠️ Module Vision inactif (Installez 'dlib' pour l'activer)")

    # 2. CONFIG CIBLE
    target_type = st.radio(
        "Mode de recherche :", 
        ["Pseudo Unique", "Identité (Prénom Nom)"],
        help="Identité va générer des variantes (ex: j.dupont, jeandupont...)"
    )
    
    user_input = st.text_input("Entrée Cible", placeholder="ex: SantaSixT ou Jean Dupont")
    
    st.markdown("### ⚙️ Modules")
    scan_tech = st.checkbox("🔍 Scan Comptes (Social/Tech)", value=True)
    use_dorking = st.checkbox("📡 Radar Hors-Piste (Dorking)", value=False)
    scan_email = st.checkbox("📧 Scan Emails Probables", value=False)
    
    with st.expander("🛠️ Options Avancées"):
        scan_adult = st.checkbox("🔞 Mode Adulte", value=False, help="Active la recherche sur les sites +18.")
        deep_analysis = st.checkbox("📸 Deep Analysis (Exif/Vision)", value=True, help="Analyse les métadonnées et compare les visages.")
    
    st.markdown("---")
    launch_btn = st.button("🚀 LANCER V6")

# --- ZONE PRINCIPALE ---
col1, col2 = st.columns([2, 1])

# INITIALISATION VISION (Si upload présent)
face_hunter = None
if VISION_AVAILABLE and uploaded_file:
    face_hunter = FaceHunter()
    success, msg = face_hunter.load_target_image(uploaded_file)
    with st.sidebar:
        if success:
            st.success("✅ Visage Encodé (Prêt)")
            st.image(uploaded_file, width=100)
        else:
            st.error(msg)

if launch_btn and user_input:
    # 1. INITIALISATION CLASSES
    scraper = GhostScraper() 
    
    # Filtre anti-faux positifs (Sites adultes)
    if not scan_adult:
        # On ne garde que les sites qui NE SONT PAS 'adult'
        scraper.sites = {k: v for k, v in scraper.sites.items() if v.get("category") != "adult"}
    else:
        st.toast("⚠️ Mode Adulte Activé : Vérifiez manuellement les résultats !", icon="🔞")

    email_gen = EmailGenerator() 
    final_results = []
    
    with col1:
        st.subheader("📡 Flux d'Investigation")
        status_area = st.empty() 
        progress_bar = st.progress(0)
        
        # 2. GÉNÉRATION VARIANTES
        if target_type == "Identité (Prénom Nom)":
            targets_to_scan = generate_usernames(user_input)
            st.info(f"🧬 Mode Générateur activé : {len(targets_to_scan)} variantes.")
        else:
            targets_to_scan = [user_input]

        # 3. SCAN COMPTES
        if scan_tech:
            total_steps = len(targets_to_scan)
            
            def update_ui(msg): status_area.code(msg)

            for i, target in enumerate(targets_to_scan):
                status_area.text(f"🔍 Scan de la variante : {target}...")
                scraper.scan_username(target, callback_status=update_ui)
                progress_bar.progress((i+1) / total_steps)
            
            final_results.extend(scraper.results)

        # 4. RADAR DORKING
        if use_dorking:
            st.markdown("---")
            status_area.warning("📡 Radar Web actif...")
            try:
                dork_results = google_dorking(user_input, email_mode=False)
                if dork_results:
                    final_results.extend(dork_results)
            except Exception as e:
                st.error(f"Erreur Dorking: {e}")

        # 5. SCAN EMAIL
        if scan_email and target_type == "Identité (Prénom Nom)":
            st.markdown("---")
            status_area.warning("📧 Génération & Test des Emails...")
            generated_emails = email_gen.generate(user_input)
            if generated_emails:
                hits = google_dorking(generated_emails, email_mode=True)
                if hits:
                    final_results.extend(hits)
                    st.error(f"⚠️ {len(hits)} emails potentiels trouvés !")

        # 6. ANALYSE PROFONDE (VISION & EXIF)
        if deep_analysis and final_results:
            st.markdown("---")
            st.subheader("🧬 Analyse Biométrique & Métadonnées")
            status_area.info("Analyse des images en cours...")
            
            for res in final_results:
                # --- ZONE DE DEBUG (Fusionnée) ---
                if 'metadata' in res and 'Avatar' in res['metadata']:
                    avatar_url = res['metadata']['Avatar']
                    # On affiche discrètement que l'image est prise en compte
                    st.caption(f"👁️ Analyse image sur : {res['site']}")
                    
                    # A. EXIF DATA (Metadata cachée)
                    exif = get_exif_data(avatar_url)
                    if exif:
                        res['metadata']['EXIF_DATA'] = str(exif)
                        st.toast(f"💾 EXIF trouvé sur {res['site']}!", icon="🕵️")

                    # B. FACE MATCHER (Reconnaissance Faciale)
                    if face_hunter and face_hunter.has_face:
                        match_data = face_hunter.compare_with_url(avatar_url)
                        
                        if match_data and "error" not in match_data:
                            score = match_data['score']
                            if match_data['match']:
                                st.markdown(f"""
                                <div class="match-success">
                                    <h3>✅ MATCH VISAGE : {score}%</h3>
                                    <strong>Sur :</strong> {res['site']} ({res['username']})<br>
                                    <img src="{avatar_url}" width="50" style="border-radius:50%;">
                                </div>
                                """, unsafe_allow_html=True)
                                res['metadata']['BIOMETRIC_CHECK'] = f"✅ MATCH {score}%"
                            elif score > 45: # Seuil de doute
                                st.warning(f"🤔 Ressemblance ({score}%) sur {res['site']}.")
                                st.image(avatar_url, width=50)
                else:
                    # DEBUG : Affiche pourquoi ça n'analyse pas
                    st.markdown(f"<span class='debug-text'>❌ Pas d'avatar récupéré pour {res['site']}</span>", unsafe_allow_html=True)

        # 7. TIMELINE (Dates dans les bios)
        dates_found = []
        for r in final_results:
            found = re.findall(r"(201[0-9]|202[0-5])", str(r))
            if found: dates_found.extend(found)
        
        if dates_found:
            st.markdown("---")
            st.subheader("⏳ Timeline Estimée")
            dates_unique = sorted(list(set(dates_found)))
            st.write("Années d'activité détectées : " + " ➡️ ".join(dates_unique))

        # 8. AFFICHAGE RÉSULTATS
        st.success(f"Investigation terminée ! {len(final_results)} traces trouvées.")
        
        if final_results:
            for res in final_results:
                icon = "🌐"
                cat = res.get('category')
                if cat == 'coding': icon = "💻"
                elif cat == 'social': icon = "🗣️"
                elif cat == 'hors-piste': icon = "🔎"
                elif cat == 'mail-leak': icon = "📧"
                elif cat == 'adult': icon = "🔞"

                with st.expander(f"{icon} {res['site']} - {res['username']}"):
                    st.markdown(f"**Lien:** [{res['url']}]({res['url']})")
                    if res.get('metadata'):
                        st.json(res['metadata'])

            # 9. CARTOGRAPHIE & GRAPHE
            st.markdown("---")
            col_map, col_graph = st.columns(2)
            
            with col_map:
                st.subheader("🌍 Géolocalisation")
                has_location = any("Location" in r.get('metadata', {}) for r in final_results)
                if has_location:
                    with st.spinner("Triangulation..."):
                        m, c = generate_map(final_results)
                        if c > 0: st_folium(m, height=300)
                else:
                    st.info("Pas de données GPS.")

            with col_graph:
                st.subheader("🕸️ Visualisation")
                try: 
                    generate_graph(final_results, user_input)
                except: 
                    st.warning("Données insuffisantes pour le graphe.")
            
            # 10. SECRET HUNTER
            st.markdown("---")
            st.subheader("⚔️ Analyse de Vulnérabilité")
            if scan_tech: 
                hunter = SecretHunter()
                leaks = hunter.analyze_results(final_results)
                if leaks:
                    st.error(f"⚠️ {len(leaks)} secrets potentiels détectés !")
                    for l in leaks: st.write(f"- {l['type']} : {l['preview']}")
                else:
                    st.success("🛡️ Aucun secret évident détecté.")

    # --- COLONNE DE DROITE (RAPPORT) ---
    with col2:
        st.subheader("📊 Rapport Consolidé")
        if final_results:
            df = pd.DataFrame(final_results)
            display_cols = [col for col in ['site', 'username', 'category'] if col in df.columns]
            st.dataframe(df[display_cols], hide_index=True)
            
            # Export JSON
            st.download_button("💾 JSON", json.dumps(final_results, indent=4), "report.json")
            
            # Export PDF
            try:
                pdf_data = generate_pdf(final_results, user_input)
                st.download_button("📄 PDF (Officiel)", pdf_data, "report.pdf")
            except Exception as e:
                st.error(f"Erreur PDF: {e}")

            # Export HTML (Dashboard)
            try:
                html_data = generate_html(final_results, user_input)
                st.download_button("💻 Dashboard HTML", html_data, "dashboard.html", mime="text/html")
            except Exception as e:
                st.error(f"Erreur HTML: {e}")

            st.metric("Total Traces", len(final_results))
            st.metric("Variantes testées", len(targets_to_scan))
            
        else:
            st.info("En attente...")
            st.image("https://media.giphy.com/media/l0HlO4p8jVpMQeI3m/giphy.gif", caption="Système prêt...", width=200)

elif launch_btn and not user_input:
    st.error("⚠️ Erreur : Veuillez entrer une cible.")