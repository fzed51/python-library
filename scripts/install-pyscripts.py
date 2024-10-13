import json
from os import path, makedirs, environ, listdir
from os.path import join, isdir, dirname
import requests

def check_env(var):
    """
    Vérifie si une variable d'environnement existe et si elle pointe vers un répertoire existant.
    Args:
        var (str): Le nom de la variable d'environnement à vérifier.
    Returns:
        bool: True si la variable existe et pointe vers un répertoire, False sinon.
    """
    if var in environ:
        path = environ[var]
        if isdir(path):
            return True
        raise f"Le chemin spécifié par la variable d'environnement {var} ({path}) n'est pas un répertoire."
    raise f"La variable d'environnement {var} n'est pas définie."

def join_url(parent, child):
    """
    Joint deux URL en supprimant les barres obliques en trop.
    """
    return f"{parent.rstrip('/')}/{child.lstrip('/')}"

def main():
    # URL du catalogue de scripts
    URL = "https://fzed51.github.io/python-library"

    # Répertoires
    check_env('PYHOME')
    check_env('PYSCRIPTS')
    script_directory = environ['PYSCRIPTS']  # Répertoire par défaut pour les scripts
    installed_script_file = join(environ['PYHOME'], "installed-script.json")

    # Téléchargement du catalogue de scripts
    response = requests.get(URL + "/scripts_catalog.json")
    catalog = json.loads(response.content)

    # Affichage du catalogue
    print("Catalogue de scripts :")
    for index, script in enumerate(catalog, start=1):
        print(f"{index} - {script['name']}")

    # Choix de l'utilisateur
    script_number = input("Entrez le numéro du script à installer (chiffres uniquement) : ")
    if not script_number.isdigit():
        print("Saisie invalide. Veuillez saisir un numéro.")
        return

    try:
        script_index = int(script_number) - 1
        script = catalog[script_index]
        print(f"Vous allez installer le script '{script['name']}'")
    except IndexError:
        print(f"Le script numéro {script_number} n'existe pas.")
        return

    # Création du répertoire des scripts s'il n'existe pas
    if not path.exists(script_directory):
        makedirs(script_directory)

    # Vérification de la présence du répertoire dans PATH
    script_path_trimmed = script_directory.rstrip("\\/")
    env_path = environ.get("PATH", "").split(";")
    env_path_trimmed = [p.rstrip("\\/") for p in env_path]
    if script_path_trimmed not in env_path_trimmed:
        env_path.append(script_path_trimmed)
        environ["PATH"] = ";".join(env_path)
        print(f"Le dossier '{script_directory}' a été ajouté aux variables d'environnement PATH.")

    # Téléchargement du script
    script_url = join_url(URL + "/library/scripts/", script["name"])
    script_path = join(script_directory, script["name"])
    response = requests.get(script_url, stream=True)
    response.raise_for_status()  # Lève une exception en cas d'erreur
    with open(script_path, 'wb') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)

    # Gestion du fichier des scripts installés
    installed_scripts = []
    if path.exists(installed_script_file):
        try:
            with open(installed_script_file, 'r') as f:
                installed_scripts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass  # Fichier vide ou invalide

    # Mise à jour de la liste des scripts installés
    installed_scripts = [s for s in installed_scripts if s["id"] != script["id"]]
    installed_scripts.append(script)

    # Sauvegarde de la liste des scripts installés
    with open(installed_script_file, 'w') as f:
        json.dump(installed_scripts, f, indent=4)  # Sauvegarde avec indentation pour lisibilité

    print(f"Le script '{script['name']}' a été installé avec succès.")

if __name__ == "__main__":
    main()
