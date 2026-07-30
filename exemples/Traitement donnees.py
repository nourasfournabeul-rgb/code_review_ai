def f(l):
    r = []
    for i in l:
        if i % 2 == 0:
            r.append(i)
    return r


def calculer_total(commandes):
    t = 0
    for c in commandes:
        for p in c["produits"]:
            t = t + p["prix"] * p["quantite"]
    return t


def trouver_doublons(liste):
    doublons = []
    for i in range(len(liste)):
        for j in range(len(liste)):
            if i != j and liste[i] == liste[j]:
                if liste[i] not in doublons:
                    doublons.append(liste[i])
    return doublons


def convertir_temperature(temp, type):
    if type == "CtoF":
        return temp * 9 / 5 + 32
    elif type == "FtoC":
        return (temp - 32) * 5 / 9
    elif type == "CtoK":
        return temp + 273.15


class gestionnairestock:
    def __init__(self):
        self.stock = {}

    def Ajouter(self, Nom, Quantite):
        if Nom in self.stock:
            self.stock[Nom] = self.stock[Nom] + Quantite
        else:
            self.stock[Nom] = Quantite

    def retirer(self, nom, quantite):
        self.stock[nom] -= quantite