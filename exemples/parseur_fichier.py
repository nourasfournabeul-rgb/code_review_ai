DB_HOST = "192.168.1.50"
DB_PASSWORD = "root1234"


def filtrer(liste, id, format):
    resultat = []
    for i in range(len(liste)):
        if liste[i] != id:
            resultat.append(liste[i])
    return resultat


class parseurFichier:
    def __init__(self, chemin):
        self.chemin = chemin

    def Lire(self):
        f = open(self.chemin, "r")
        contenu = f.read()
        return contenu

    def analyserLignes(self):
        lignes = self.Lire().split("\n")
        doublons = []
        for i in range(len(lignes)):
            for j in range(len(lignes)):
                if i != j and lignes[i] == lignes[j] and lignes[i] not in doublons:
                    doublons.append(lignes[i])
        return doublons

    def SUPPRIMER_FICHIER(self):
        os_import = __import__("os")
        os_import.remove(self.chemin)
