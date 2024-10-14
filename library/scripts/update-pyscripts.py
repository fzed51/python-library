import requests
import json
import os
import uuid
from urllib.parse import urljoin
from os.path import join
from os import remove, environ
from hashlib import sha256


def join_url(parent, child):
    """
    Joint deux URL en supprimant les barres obliques en trop.
    """
    return f"{parent.rstrip('/')}/{child.lstrip('/')}"


def download_json(url: str):
    """
    Télécharge un fichier au format json
    :param url: Url de téléchargement
    :return: donnée du json
    """
    response = requests.get(url)
    response.raise_for_status()
    return json.loads(response.content)


def download(url: str, save_path: str, expected_hash: str | None = None) -> None:
    """
    Rélécharge le un fichier et vérifie son hash
    :param url: url de téléchargement
    :param save_path: nom sous le quel est enregistré le fichier
    :param expected_hash: hash dez validation (optional)
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    hasher = sha256()
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(1024):
            hasher.update(chunk)
            f.write(chunk)

    calculated_hash = hasher.hexdigest()
    if expected_hash and calculated_hash != expected_hash:
        remove(save_path)
        raise ValueError("Hash mismatch")


def update_script(old_script: dict, new_script: dict, installed_scripts: list, script_directory: str):
    """
    Updates a script in the script directory.
    :param old_script: Dictionary representing the old script information.
    :param new_script: Dictionary representing the new script information.
    :param installed_scripts: List of dictionaries representing installed scripts.
    :param script_directory: Chemin où sont installé les scripts.
    :return: Updated list of installed scripts.
    """
    registry_library = "https://fzed51.github.io/python-library/library/scripts/"
    temp_filename = str(uuid.uuid4())
    temp_path = join(script_directory, temp_filename)

    # Move the old script to a temporary file
    os.rename(join(script_directory, old_script["name"]), temp_path)

    # Filter installed scripts excluding the old one
    installed_scripts = [
        script for script in installed_scripts if script["id"] != old_script["id"]
    ]

    # Download the new script
    url = urljoin(registry_library, new_script["name"])
    try:
        response = requests.get(url)
        response.raise_for_status()

        with open(join(script_directory, new_script["name"]), "wb") as f:
            f.write(response.content)

        # Delete the temporary file
        os.remove(temp_path)

        print(f"{old_script['name']} has been updated")
        print(f"{old_script['version']} -> {new_script['version']}")

        installed_scripts.append(new_script)
    except requests.exceptions.RequestException as e:
        print(f"Error updating {old_script['name']}: {e}")
        # Log additional information (version, URL, error message)
        print(f"Current version: {old_script['version']}, New version: {new_script['version']}")
        print(f"URL: {url}")
        print(f"Error: {e}")

        # Move the temporary file back to the original name
        os.rename(temp_path, join(script_directory, old_script["name"]))

    return installed_scripts


def main():
    # Script configuration (modify as needed)
    script_directory = environ['PYSCRIPTS']
    installed_script_file = join(environ['PYHOME'], "installed-script.json")

    # Download script catalog
    catalog_url = "https://fzed51.github.io/powershell-library/scripts_catalog.json"
    try:
        catalog = download_json(catalog_url)
    except Exception as e:
        print(f"Error retrieving script catalog: {e}")
        exit(1)

    # Load installed scripts (empty list if not found)
    installed_scripts = []
    try:
        with open(installed_script_file, "r") as f:
            installed_scripts = json.load(f)
    except FileNotFoundError:
        print("Une erreur est survenue lors de la récupération de la liste des fichiers déjà téléchargés.")
        exit(1)

    # Update scripts
    new_installed_scripts = installed_scripts.copy()
    for installed_script in installed_scripts:
        matching_script = next(
            (script for script in catalog if script["id"] == installed_script["id"]), None
        )
        if matching_script and matching_script["version"] != installed_script["version"]:
            new_installed_scripts = update_script(
                installed_script, matching_script, new_installed_scripts, script_directory
            )

    # Save updated installed scripts
    with open(installed_script_file, "w") as f:
        json.dump(new_installed_scripts, f, indent=4)

    print("Script update completed!")


if __name__ == "__main__":
    main()
