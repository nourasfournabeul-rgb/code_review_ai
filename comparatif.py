"""
Script de comparatif automatise entre plusieurs modeles Ollama.
Teste chaque fichier d'exemple sur chaque modele, pour les 4 fonctionnalites,
mesure le temps de reponse, et sauvegarde tout dans un fichier de resultats.
"""

import requests
import time
import json
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELES = ["llama3.2", "gemma2"]
DOSSIER_EXEMPLES = Path("exemples")
FICHIER_RESULTATS = "resultats_comparatif.json"

LANGAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
}

PROMPTS = {
    "expliquer": lambda code, language: f"""Tu es un expert en developpement logiciel.
Explique de maniere claire et concise ce que fait le code source suivant ({language}).
Decris sa logique globale, les fonctions principales, et l'objectif general du fichier.
Reponds en francais.

Code source ({language}) :
{code}
""",
    "Mauvaises_pratiques": lambda code, language: f"""Tu es un expert en qualite de code et securite logicielle, tous langages confondus.
Analyse le code source suivant ({language}) et verifie les points suivants :
- Convention de nommage (classes, fonctions, variables) et leur coherence dans tout le fichier
- Utilisation de noms qui entrent en conflit avec des mots-cles ou noms reserves du langage
- Complexite algorithmique des boucles (boucles imbriquees inutiles, recherches repetees)
- Gestion des cas ou une cle/valeur/element recherche n'existe pas (risque d'erreur silencieuse)
- Securite (donnees sensibles en dur, entrees non validees, injection)
- Gestion d'erreurs et robustesse generale

IMPORTANT : pour chaque point de la liste, si tu ne trouves AUCUN probleme reel et verifiable
dans le code, ecris explicitement "Aucun probleme detecte sur ce point" plutot que d'inventer
un probleme. Ne signale que des problemes reellement presents dans le code fourni, avec la
ligne ou fonction exacte concernee.

Reponds en francais.

Code source ({language}) :
{code}
""",
    "ameliorations": lambda code, language: f"""Tu es un expert en refactoring de code.
Propose des ameliorations concretes pour le code source suivant ({language}).
Pour chaque suggestion, explique brievement pourquoi c'est mieux.
Presente ta reponse sous forme de liste a puces. Reponds en francais.

Code source ({language}) :
{code}
""",
    "resume": lambda code, language: f"""Tu es un expert en developpement logiciel.
Genere un resume court (4 a 6 lignes maximum) du code source suivant ({language}) :
son role global, ses points forts et ses points faibles principaux.
Reponds en francais.

Code source ({language}) :
{code}
""",
}


# --------------------------------------------------------------------------
# Fonctions
# --------------------------------------------------------------------------

def appeler_ollama(prompt: str, modele: str) -> tuple[str, float]:
    """Envoie un prompt a Ollama et renvoie (reponse, temps_ecoule_en_secondes)."""
    debut = time.time()
    try:
        reponse = requests.post(
            OLLAMA_URL,
            json={"model": modele, "prompt": prompt, "stream": False},
            timeout=180,
        )
        reponse.raise_for_status()
        texte = reponse.json()["response"].strip()
        duree = round(time.time() - debut, 2)
        return texte, duree
    except Exception as e:
        duree = round(time.time() - debut, 2)
        return f"ERREUR : {str(e)}", duree


def lancer_comparatif():
    if not DOSSIER_EXEMPLES.exists():
        print(f"Le dossier '{DOSSIER_EXEMPLES}' n'existe pas. Cree-le et ajoute des fichiers de code dedans.")
        return

    fichiers = [
        chemin for chemin in DOSSIER_EXEMPLES.iterdir()
        if chemin.is_file() and chemin.suffix in LANGAGES
    ]
    if not fichiers:
        extensions = ", ".join(sorted(set(LANGAGES.keys())))
        print(f"Aucun fichier de langage supporte trouve dans '{DOSSIER_EXEMPLES}'. Extensions attendues : {extensions}.")
        return

    resultats = []

    for fichier in fichiers:
        code = fichier.read_text(encoding="utf-8")
        language = LANGAGES.get(fichier.suffix, "Inconnu")
        print(f"\n=== Fichier : {fichier.name} ({language}) ===")

        for modele in MODELES:
            print(f"  -> Modele : {modele}")

            for nom_tache, construire_prompt in PROMPTS.items():
                print(f"     - Tache : {nom_tache}...", end=" ")
                prompt = construire_prompt(code, language)
                reponse, duree = appeler_ollama(prompt, modele)
                print(f"OK ({duree}s)")

                resultats.append({
                    "fichier": fichier.name,
                    "langage": language,
                    "modele": modele,
                    "tache": nom_tache,
                    "duree_secondes": duree,
                    "reponse": reponse,
                })

    with open(FICHIER_RESULTATS, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    print(f"\n Termine. Resultats sauvegardes dans '{FICHIER_RESULTATS}'")

    afficher_resume_temps(resultats)


def afficher_resume_temps(resultats: list[dict]):
    """Affiche un petit resume des temps moyens par modele."""
    print("\n=== Resume des temps de reponse moyens ===")
    for modele in MODELES:
        temps = [r["duree_secondes"] for r in resultats if r["modele"] == modele]
        if temps:
            moyenne = round(sum(temps) / len(temps), 2)
            print(f"{modele} : {moyenne}s en moyenne sur {len(temps)} appels")

    print("\n=== Resume des temps moyens par langage ===")
    langues = sorted({r["langage"] for r in resultats})
    for langage in langues:
        temps = [r["duree_secondes"] for r in resultats if r["langage"] == langage]
        if temps:
            moyenne = round(sum(temps) / len(temps), 2)
            print(f"{langage} : {moyenne}s en moyenne sur {len(temps)} appels")


# --------------------------------------------------------------------------
# Lancement
# --------------------------------------------------------------------------

if __name__ == "__main__":

    lancer_comparatif()