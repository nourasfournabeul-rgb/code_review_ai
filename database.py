import os

import pymysql
import pymysql.cursors

# ==============================
# Configuration de connexion
# ==============================
# Valeurs par defaut utilisees si les variables d'environnement
# correspondantes ne sont pas definies. Adaptez-les a votre installation
# MySQL (independante, XAMPP, etc.).

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "nourasfour2005")
DB_NAME = os.environ.get("DB_NAME", "code_review_ai")


def get_connection(avec_base: bool = True) -> pymysql.connections.Connection:
    """
    Ouvre une connexion MySQL.
    avec_base=False permet de se connecter au serveur sans selectionner la
    base (utile pour la creer si elle n'existe pas encore).
    """
    parametres = dict(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

    if avec_base:
        parametres["database"] = DB_NAME

    try:
        return pymysql.connect(**parametres)
    except pymysql.err.OperationalError as e:
        raise RuntimeError(
            "Impossible de se connecter a MySQL. Verifiez que le serveur "
            "MySQL est bien demarre, et que DB_HOST / DB_PORT / DB_USER / "
            "DB_PASSWORD (variables d'environnement ou valeurs par defaut "
            f"dans database.py) correspondent a votre installation. Detail : {e}"
        ) from e


def init_db() -> None:
    """
    Cree la base 'code_review_ai' si elle n'existe pas encore, puis la
    table 'users' a l'interieur.
    """
    # 1. Creation de la base si necessaire (connexion sans base selectionnee)
    conn = get_connection(avec_base=False)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()

    # 2. Creation de la table 'users' si necessaire
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(150) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
    finally:
        conn.close()


def get_user_by_username(username: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s", (username,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def create_user(username: str, password_hash: str) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
    finally:
        conn.close()