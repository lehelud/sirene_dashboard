"""
setup_auth.py
-------------
Script interactif pour creer ou mettre a jour les comptes utilisateurs.
Genere le fichier auth_config.yaml avec les mots de passe hashes.

Usage :
    python setup_auth.py
"""

import yaml
import getpass
from pathlib import Path
import streamlit_authenticator as stauth

CONFIG_PATH = Path("auth_config.yaml")


def hasher_mot_de_passe(mdp: str) -> str:
    """Hash un mot de passe avec bcrypt via streamlit-authenticator."""
    return stauth.Hasher([mdp]).generate()[0]


def creer_config_defaut() -> dict:
    """Cree une configuration avec un compte admin par defaut."""
    print("\n=== Creation des comptes utilisateurs ===\n")
    utilisateurs = {}
    continuer = True
    while continuer:
        print("Nouvel utilisateur :")
        nom = input("  Nom complet : ").strip()
        email = input("  Email : ").strip()
        username = input("  Nom d'utilisateur (login) : ").strip().lower()
        mdp = getpass.getpass("  Mot de passe : ")
        mdp_confirm = getpass.getpass("  Confirmer le mot de passe : ")
        if mdp != mdp_confirm:
            print("  Les mots de passe ne correspondent pas, recommence.")
            continue
        mdp_hash = hasher_mot_de_passe(mdp)
        utilisateurs[username] = {
            "email": email, "name": nom, "password": mdp_hash,
            "role": "admin", "failed_login_attempts": 0, "logged_in": False,
        }
        print(f"  Compte '{username}' cree.\n")
        rep = input("Ajouter un autre utilisateur ? (o/N) : ").strip().lower()
        continuer = rep in ("o", "oui", "y", "yes")
    config = {
        "credentials": {"usernames": utilisateurs},
        "cookie": {"expiry_days": 7, "key": _generer_cle_secrete(), "name": "sirene_dashboard_auth"},
        "pre-authorized": {"emails": [u["email"] for u in utilisateurs.values()]},
    }
    return config


def _generer_cle_secrete() -> str:
    """Genere une cle secrete aleatoire pour les cookies."""
    import secrets
    return secrets.token_hex(32)


def main():
    print("=" * 50)
    print("  SIRENE Dashboard - Configuration authentification")
    print("=" * 50)
    if CONFIG_PATH.exists():
        rep = input(
            f"\nLe fichier {CONFIG_PATH} existe deja.\n"
            "  (r) Reinitialiser completement\n"
            "  (a) Ajouter un utilisateur\n"
            "  Choix (r/a) : "
        ).strip().lower()
        if rep == "a":
            from yaml.loader import SafeLoader
            with open(CONFIG_PATH) as f:
                config = yaml.load(f, Loader=SafeLoader)
            print("\nAjout d'un utilisateur :")
            nom = input("  Nom complet : ").strip()
            email = input("  Email : ").strip()
            username = input("  Nom d'utilisateur : ").strip().lower()
            mdp = getpass.getpass("  Mot de passe : ")
            mdp_hash = hasher_mot_de_passe(mdp)
            config["credentials"]["usernames"][username] = {
                "email": email, "name": nom, "password": mdp_hash,
                "role": "user", "failed_login_attempts": 0, "logged_in": False,
            }
            if email not in config.get("pre-authorized", {}).get("emails", []):
                config.setdefault("pre-authorized", {}).setdefault("emails", []).append(email)
            print(f"  Utilisateur '{username}' ajoute.")
        else:
            config = creer_config_defaut()
    else:
        config = creer_config_defaut()
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    print(f"\nConfiguration sauvegardee dans {CONFIG_PATH}")
    print("\nIMPORTANT : n'ajoute PAS auth_config.yaml dans Git !")
    print("   Verifie que '.gitignore' contient bien : auth_config.yaml")
    print("\nLance maintenant : streamlit run app.py")


if __name__ == "__main__":
    main()
