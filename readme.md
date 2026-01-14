# 👻 GhostTracker - OSINT & Reconnaissance Tool

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Interface-Streamlit-red)
![Security](https://img.shields.io/badge/Focus-DevSecOps-green)

GhostTracker est un outil de **Reconnaissance Offensive (OSINT)** développé dans un cadre éducatif. Il permet d'automatiser la collecte d'informations sur une cible à partir d'un simple pseudo ou d'une identité réelle.

## 🚀 Fonctionnalités

- **🧬 Générateur d'Identités :** Création automatique de variantes de pseudos (ex: `j.dupont`, `jeandupont`...) à partir d'un nom réel.
- **🕵️ Scraper Multi-Sources :** Scan rapide de comptes (GitHub, Twitter, Instagram, DockerHub, Pastebin...).
- **📡 Radar Hors-Piste (Dorking) :** Recherche avancée via DuckDuckGo pour trouver des traces hors réseaux sociaux (PDF, Blogs, Leaks...).
- **🌍 Géolocalisation Tactique :** Extraction des villes dans les bios et affichage sur une carte interactive.
- **⚔️ Secret Hunter :** Analyse heuristique (Regex) pour détecter des fuites de secrets (Clés API, Emails pro, Mots de passe).

## 🛠️ Installation

1. **Cloner le dépôt :**
   ```bash
   git clone [https://github.com/TON_USER/GhostTracker.git](https://github.com/TON_USER/GhostTracker.git)
   cd GhostTracker

2. **Créer un environnement virtuel (Recommandé) :**
    python -m venv venv
    source venv/bin/activate  # Sur Linux/Mac
    # venv\Scripts\activate   # Sur Windows
3. **Installer les dépendances :**
    pip install -r requirements.txt

**🎮 Utilisation**
Lancez le Cockpit via Streamlit :
streamlit run app.py

L'interface s'ouvrira automatiquement dans votre navigateur.

    Choisissez le mode (Pseudo ou Identité).

    Entrez la cible.

    Activez les modules (Dorking, Tech Focus).

    Lancez l'investigation.

⚠️ Avertissement Légal

Ce projet est conçu à des fins éducatives et de recherche en sécurité uniquement. L'utilisateur est seul responsable de l'utilisation qu'il fait de cet outil. N'utilisez pas ce logiciel pour harceler ou attaquer des cibles sans autorisation explicite.

Développé par SantaSixT - Projet DevSecOps