"""
Module github_manager.py
Contient des fonctions pour interagir avec l'API GitHub.
"""

# Vous pouvez ajouter votre token GitHub dans une variable d'environnement ou
# le passer en argument aux fonctions.

def get_user_repos(token, username):
    """Renvoie la liste des dépôts d'un utilisateur GitHub."""
    import requests
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
