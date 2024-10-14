#! python3

import hashlib
import json
import sys
import uuid


def get_sha256(path):
    """
    Donne le sha 256 d'un fichier
    :param path:  chemin du fichier
    :return: sha256 hexadecimal
    """
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)

    return hasher.hexdigest()

def get_name(path):
    return path.replace("\\", "/").split("/")[-1]

def main(path):
    registre = {
        "id": str(uuid.uuid4()),
        "name": get_name(path),
        "hash": get_sha256(path),
        "version": "1.0.0"
    }
    print(f"Registre de {path} : ")
    print (json.dumps(registre, separators=(',', ':'), indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Veuillez fournir le chemin du fichier en argument.")
        sys.exit(1)
    main(sys.argv[1])
