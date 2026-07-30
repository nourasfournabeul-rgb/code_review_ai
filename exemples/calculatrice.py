password = "admin123"


def calc(a, b, x):
    if x == 1:
        return a + b
    if x == 2:
        return a - b
    if x == 3:
        return a * b
    if x == 4:
        return a / b


def getData():
    global password
    return password


def traiter(liste):
    resultat = []
    for i in range(len(liste)):
        if liste[i] not in resultat:
            resultat.append(liste[i])
    return resultat