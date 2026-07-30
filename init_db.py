
import getpass

import bcrypt

from database import create_user, get_user_by_username, init_db


def main() -> None:
    try:
        init_db()
    except RuntimeError as e:
        print(f"Erreur : {e}")
        return

    username = input("Nom d'utilisateur : ").strip()
    password = getpass.getpass("Mot de passe : ")

    if not username or not password:
        print("Nom d'utilisateur et mot de passe requis.")
        return

    if get_user_by_username(username) is not None:
        print(f"L'utilisateur '{username}' existe deja.")
        return

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    create_user(username, password_hash)

    print(f"Utilisateur '{username}' cree avec succes.")


if __name__ == "__main__":
    main()