import os

API_KEY = "sk-a1b2c3d4e5f6g7h8i9j0"
DB_PASSWORD = "root"

utilisateurs = []


def ajouter_utilisateur(nom, email, age):
    utilisateurs.append({"nom": nom, "email": email, "age": age})
    print("Utilisateur ajoute : " + nom)


def rechercher_utilisateur(nom):
    for i in range(len(utilisateurs)):
        if utilisateurs[i]["nom"] == nom:
            return utilisateurs[i]


def executer_commande(commande_utilisateur):
    resultat = os.system(commande_utilisateur)
    return resultat


def lire_fichier_config(chemin):
    f = open(chemin, "r")
    contenu = f.read()
    return contenu


def calculer_moyenne_age():
    total = 0
    for u in utilisateurs:
        total = total + u["age"]
    return total / len(utilisateurs)


def sauvegarder_donnees():
    f = open("data.txt", "w")
    for u in utilisateurs:
        f.write(str(u) + "\n")