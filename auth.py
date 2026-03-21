fix: auth compatible Streamlit Cloud (st.secrets) et local (yaml)"""
auth.py
-------
Module d'authentification pour le dashboard SIRENE.
Utilise streamlit-authenticator avec comptes Google/email.

Usage dans app.py :
    from auth import verifier_authentification
    verifier_authentification()  # bloque si non connecte
"""

import yaml
from pathlib import Path
from yaml.loader import SafeLoader

import streamlit as st
import streamlit_authenticator as stauth

CONFIG_PATH = Path("auth_config.yaml")


def charger_config() -> dict:
    """Charge la configuration d'authentification."""
    if not CONFIG_PATH.exists():
        st.error("Fichier auth_config.yaml manquant.")
        st.info(
            "Cree ce fichier en lancant : python setup_auth.py\n"
            "ou copie auth_config.example.yaml et adapte-le."
        )
        st.stop()

    with open(CONFIG_PATH) as f:
        return yaml.load(f, Loader=SafeLoader)


def verifier_authentification() -> stauth.Authenticate:
    """
    Verifie que l'utilisateur est authentifie.
    Bloque l'acces et affiche le formulaire de login sinon.
    Retourne l'objet authenticator pour permettre le logout.
    """
    config = charger_config()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    authenticator.login(location="main")

    if st.session_state.get("authentication_status") is False:
        st.error("Identifiant ou mot de passe incorrect.")
        st.stop()

    elif st.session_state.get("authentication_status") is None:
        st.warning("Veuillez vous connecter pour acceder au dashboard.")
        _afficher_page_accueil()
        st.stop()

    with st.sidebar:
        st.markdown(f"Connecte : **{st.session_state.get('name', '')}**")
        authenticator.logout("Se deconnecter", location="sidebar")

    return authenticator


def _afficher_page_accueil():
    """Page d'accueil avant connexion."""
    st.markdown(
        """
        <div style='text-align:center; padding: 3rem 0;'>
            <h1>Dashboard SIRENE</h1>
            <p style='font-size:1.2rem; color:#666;'>
                Analyse des entreprises du secteur marchand - Base SIRENE data.gouv.fr
            </p>
            <p style='color:#999;'>Acces reserve - Connectez-vous ci-dessus</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
