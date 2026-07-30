"""
Assistant IA de revue de code
Utilise Ollama (modele local) + FastAPI pour analyser du code source.
"""

import requests
import subprocess
import time
import json
import bcrypt
from fastapi import FastAPI, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel

from database import init_db, get_user_by_username


BASE_DIR = Path(__file__).resolve().parent
OLLAMA_URL = "http://localhost:11434/api/generate"

MODELE_PAR_DEFAUT = "llama3.2"
MODELE_JUGE_PAR_DEFAUT = "qwen2.5"
PROMPTS_ACTIFS: dict[str, str] = {}
PROMPTS_TEST: dict[str, str] = {}
TACHES_VALIDES = {
    "expliquer",
    "mauvaises_pratiques",
    "ameliorations",
    "resume",
}

class ComparaisonRequest(BaseModel):
    code_source: str
    texte_llama: str
    texte_gemma: str
    modele_juge: str = MODELE_JUGE_PAR_DEFAUT


class PromptPersonnaliseRequest(BaseModel):
    prompt: str
    modele: str = MODELE_PAR_DEFAUT

class ComparaisonPromptRequest(BaseModel):
    prompt_a: str
    prompt_b: str
    modele_juge: str = MODELE_JUGE_PAR_DEFAUT

class ActiverPromptRequest(BaseModel):
    tache: str
    prompt_template: str

class ClassificationPromptRequest(BaseModel):
    prompt: str
    contexte_prompts: list[str] = []
    modele_juge: str = MODELE_JUGE_PAR_DEFAUT

class RestaurerPromptRequest(BaseModel):
    tache: str

class LoginRequest(BaseModel):
    username: str
    password: str

app = FastAPI(
    title="Assistant IA de revue de code",
    description="Analyse de fichiers source avec un LLM local (Ollama)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sert les fichiers statiques (css, js) sous /static/...
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

def ollama_est_actif() -> bool:
    try:
        reponse = requests.get("http://localhost:11434", timeout=2)
        return reponse.status_code == 200
    except requests.exceptions.RequestException:
        return False


@app.on_event("startup")
def initialiser_base_de_donnees():
    init_db()


@app.on_event("startup")
def demarrer_ollama_si_necessaire():
    if ollama_est_actif():
        print("Ollama est deja actif.")
        return

    print("Ollama n'est pas actif, tentative de demarrage automatique...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("ATTENTION : la commande 'ollama' est introuvable.")
        return

    for _ in range(15):
        time.sleep(1)
        if ollama_est_actif():
            print("Ollama a demarre avec succes.")
            return

    print("ATTENTION : Ollama n'a pas repondu apres 15 secondes.")

def appeler_ollama(prompt: str,modele: str = MODELE_PAR_DEFAUT,timeout: int = 120,num_ctx: int = 4096,format_json: bool = False) -> str:
    try:
        requete = {
            "model": modele,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": num_ctx
            }
        }

        if format_json:
            requete["format"] = "json"

        reponse = requests.post(
            OLLAMA_URL,
            json=requete,
            timeout=timeout,
        )

        reponse.raise_for_status()
        return reponse.json()["response"].strip()

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Impossible de contacter Ollama. Verifie qu'il tourne bien."
        )

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Le modele a mis trop de temps a repondre."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur Ollama : {str(e)}"
        )

def prompt_expliquer(code: str) -> str:
    return f"""Tu es un expert en developpement logiciel.
Explique de maniere claire et concise ce que fait le code source suivant.
Decris sa logique globale, les fonctions principales, et l'objectif general du fichier.
Reponds en francais.

Code source :
{code}
"""


def prompt_mauvaises_pratiques(code: str) -> str:
    return f"""Tu es un expert en qualite de code et securite logicielle, tous langages confondus.
Analyse le code source suivant et verifie les points suivants :
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

Code source :
{code}
"""


def prompt_ameliorations(code: str) -> str:
    return f"""Tu es un expert en refactoring de code.
Propose des ameliorations concretes pour le code source suivant.
Pour chaque suggestion, explique brievement pourquoi c'est mieux.
Presente ta reponse sous forme de liste a puces. Reponds en francais.

Code source :
{code}
"""


def prompt_resume(code: str) -> str:
    return f"""Tu es un expert en developpement logiciel.
Genere un resume court (4 a 6 lignes maximum) du code source suivant :
son role global, ses points forts et ses points faibles principaux.
Reponds en francais.

Code source :
{code}
"""

def construire_prompt(tache: str, code: str, prompt_fn) -> str:

    # priorité au prompt temporaire de test
    if tache in PROMPTS_TEST:
        return PROMPTS_TEST[tache].replace("{code}", code)

    # sinon prompt personnalisé activé
    if tache in PROMPTS_ACTIFS:
        return PROMPTS_ACTIFS[tache].replace("{code}", code)

    # sinon prompt par défaut
    return prompt_fn(code)


def prompt_comparer(code_source: str, texte_llama: str, texte_gemma: str) -> str:
    return f"""Tu es un expert en revue de code charge de verifier objectivement deux analyses
produites par deux modeles d'IA sur le meme fichier source.


IMPORTANT :
Tu disposes du CODE SOURCE ORIGINAL.
Le code source est la seule verite de reference.

Tu ne dois PAS faire confiance aux analyses.
Tu dois verifier toi-meme chaque affirmation en la confrontant directement au code.

Tu n'es PAS un evaluateur de style.
Tu es un VERIFICATEUR FACTUEL.

Code source original :
---
{code_source}
---

Analyse du premier modele (llama3.2) :
---
{texte_llama}
---

Analyse du second modele (gemma2) :
---
{texte_gemma}
---

Pour CHAQUE affirmation importante des deux analyses :

- recopie l'affirmation exactement telle qu'elle est ecrite (sans la reformuler) ;
- si une amelioration ou un extrait de code est propose, recopie egalement ce code ;
- verifie si cette affirmation est vraie ou fausse en la comparant au code source ;
- si une correction est proposee, verifie egalement qu'elle est techniquement correcte.

Pour verifier une correction ou un extrait de code, controle notamment :

- la syntaxe ;
- la logique ;
- le respect du langage du fichier ;
- que le correctif resout bien le probleme annonce ;
- qu'il n'introduit aucun nouveau bug ;
- qu'il ne modifie pas incorrectement le comportement du programme.

Si une correction est invalide, explique precisement pourquoi.

Si une affirmation est correcte mais que la correction proposee est fausse,
le verdict doit etre "faux".

Tu dois verifier toi-meme :

- les variables ;
- les fonctions ;
- les classes ;
- les imports ;
- les boucles ;
- les conditions ;
- les exceptions ;
- les conventions de nommage (snake_case, PascalCase, camelCase...) ;
- les performances ;
- les problemes de securite ;
- les ameliorations proposees.

INTERDICTIONS ABSOLUES :

- ne jamais inventer une affirmation ;
- ne jamais resumer plusieurs affirmations en une seule ;
- ne jamais reformuler une affirmation ;
- ne jamais ajouter une suggestion absente des analyses ;
- ne jamais supposer un comportement qui n'apparait pas dans le code.

Si une analyse contient une affirmation manifestement fausse ou une correction invalide,
cela doit apparaitre dans le verdict.

Reponds UNIQUEMENT avec un objet JSON valide.

Ne mets aucun texte avant ou apres le JSON.

Le format est OBLIGATOIRE :

{{
  "affirmations_llama": [
    {{
      "affirmation": "...copie exacte de l'affirmation...",
      "code_propose": "...laisser vide si aucun code n'est propose...",
      "verdict": "vrai ou faux",
      "raison": "explication courte et basee uniquement sur le code source",
      "correction_valide": "oui, non ou non applicable"
    }}
  ],

  "affirmations_gemma": [
    {{
      "affirmation": "...copie exacte de l'affirmation...",
      "code_propose": "...laisser vide si aucun code n'est propose...",
      "verdict": "vrai ou faux",
      "raison": "explication courte et basee uniquement sur le code source",
      "correction_valide": "oui, non ou non applicable"
    }}
  ],

  "verdict_final": "indiquer quelle analyse est la plus fiable en tenant compte de toutes les affirmations et de la validite des corrections proposees"
}}

IMPORTANT :

Une affirmation correcte = verdict "vrai".

Une affirmation fausse = verdict "faux".

Une correction techniquement incorrecte = correction_valide = "non" et le verdict de cette affirmation doit etre "faux".

Une correction qui introduit un nouveau bug doit etre consideree comme fausse.

Une proposition de code qui ne resout pas le probleme annonce doit etre consideree comme fausse.

Reponds en francais.
"""
def prompt_comparer_prompts(prompt_a: str, prompt_b: str) -> str:
    return f"""Tu es un expert en conception et evaluation de prompts pour grands modeles.

Tu dois comparer deux versions de prompt A et B selon les criteres suivants :
- la clarté
- la précision
- la structure
- l'absence d'ambiguïté
- la qualité des instructions
- la présence de contraintes utiles
- la capacité du prompt à guider efficacement un LLM

N'évalue PAS la longueur comme critère de qualité en soi.

Prompt A :
---
{prompt_a}
---

Prompt B :
---
{prompt_b}
---

Réponds UNIQUEMENT avec un objet JSON valide sans aucun texte supplémentaire :
{{
  "gagnant": "a",
  "raison": "Explication courte et précise du choix."
}}

"gagnant" doit valoir exactement "a" ou "b".
"""
def prompt_classifier(prompt: str, contexte_prompts: list[str]) -> str:
    comparaison = "\n\n".join(
        [
            f"Prompt {i+1} :\n{p}"
            for i, p in enumerate(contexte_prompts)
        ]
    )
    return f"""Tu es un expert en prompt engineering.

Tu dois classifier un prompt destiné à un assistant IA de revue de code.

Analyse son objectif principal.

Important : le prompt gagnant peut être ambigu s'il est considéré seul.
Utilise l'ensemble des variantes de prompts évaluées comme contexte pour inférer l'intention commune.
Le but est de déterminer la catégorie la plus probable du groupe de prompts, pas seulement du prompt gagnant isolé.

Les catégories possibles sont :

- expliquer :
  Le prompt demande de comprendre, décrire ou expliquer le fonctionnement du code.

- mauvaises_pratiques :
  Le prompt demande de détecter des erreurs, bugs, vulnérabilités,
  problèmes de qualité ou mauvaises pratiques.

- ameliorations :
  Le prompt demande de proposer des modifications, optimisations,
  refactorings ou améliorations du code.

- resume :
  Le prompt demande une synthèse courte du code.

Un prompt peut correspondre à plusieurs catégories.
Choisis une catégorie principale et indique les catégories secondaires éventuelles.

Voici les variantes de prompts qui ont été évaluées :

---
{comparaison}
---

Le prompt gagnant est :

---
{prompt}
---

Réponds UNIQUEMENT avec un JSON valide.

Format obligatoire :

{{
  "categorie_principale": "ameliorations",
  "categories_secondaires": [
      "mauvaises_pratiques"
  ],
  "confiance": 0.90,
  "raison": "Explication courte du choix."
}}

Règles :
- categorie_principale doit être une des quatre catégories.
- categories_secondaires peut être vide.
- confiance doit être comprise entre 0 et 1.
- Ne retourne aucun texte avant ou après le JSON.
"""
def extraire_json(texte: str):
    """
    Tente de parser le texte comme JSON. Si le modele a ajoute du texte parasite
    avant/apres l'objet JSON, on essaie de retrouver juste la portion { ... }.
    Renvoie None si aucun JSON valide n'a pu etre extrait.
    """
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        pass

    debut = texte.find("{")
    fin = texte.rfind("}")
    if debut != -1 and fin != -1 and fin > debut:
        try:
            return json.loads(texte[debut:fin + 1])
        except json.JSONDecodeError:
            return None
    return None

async def lire_fichier(fichier: UploadFile) -> str:
    contenu_brut = await fichier.read()
    try:
        return contenu_brut.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Le fichier doit etre un fichier texte/code valide (UTF-8).")

 
@app.get("/")
def accueil():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))

@app.get("/login")
def login_page():
    return FileResponse(str(BASE_DIR / "static" / "login.html"))

@app.post("/login")
async def login(payload: LoginRequest):
    utilisateur = get_user_by_username(payload.username)

    mot_de_passe_valide = utilisateur is not None and bcrypt.checkpw(
        payload.password.encode("utf-8"),
        utilisateur["password_hash"].encode("utf-8"),
    )

    if not mot_de_passe_valide:
        raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect")

    return {"message": "Connexion réussie"}

@app.post("/expliquer")
async def expliquer(
    fichier: UploadFile,
    modele: str = MODELE_PAR_DEFAUT,
    prompt_test: str = Form(None),
):
    code = await lire_fichier(fichier)

    if prompt_test:
        prompt = prompt_test.replace("{code}", code)
    else:
        prompt = construire_prompt("expliquer", code, prompt_expliquer)

    resultat = appeler_ollama(prompt, modele)

    return {
        "fichier": fichier.filename,
        "modele": modele,
        "explication": resultat
    }


@app.post("/mauvaises-pratiques")
async def mauvaises_pratiques(
    fichier: UploadFile,
    modele: str = MODELE_PAR_DEFAUT,
    prompt_test: str = Form(None),
):
    code = await lire_fichier(fichier)

    if prompt_test:
        prompt = prompt_test.replace("{code}", code)
    else:
        prompt = construire_prompt("mauvaises_pratiques", code, prompt_mauvaises_pratiques)

    resultat = appeler_ollama(prompt, modele)

    return {
        "fichier": fichier.filename,
        "modele": modele,
        "mauvaises_pratiques": resultat
    }


@app.post("/ameliorations")
async def ameliorations(
    fichier: UploadFile,
    modele: str = MODELE_PAR_DEFAUT,
    prompt_test: str = Form(None),
):
    code = await lire_fichier(fichier)

    if prompt_test:
        prompt = prompt_test.replace("{code}", code)
    else:
        prompt = construire_prompt("ameliorations", code, prompt_ameliorations)

    resultat = appeler_ollama(prompt, modele)

    return {
        "fichier": fichier.filename,
        "modele": modele,
        "ameliorations": resultat
    }


@app.post("/resume")
async def resume(
    fichier: UploadFile,
    modele: str = MODELE_PAR_DEFAUT,
    prompt_test: str = Form(None),
):
    code = await lire_fichier(fichier)

    if prompt_test:
        prompt = prompt_test.replace("{code}", code)
    else:
        prompt = construire_prompt("resume", code, prompt_resume)

    resultat = appeler_ollama(prompt, modele)

    return {
        "fichier": fichier.filename,
        "modele": modele,
        "resume": resultat
    }

@app.post("/expliquer-personnalise")
async def expliquer_personnalise(payload: PromptPersonnaliseRequest):
    resultat = appeler_ollama(payload.prompt, payload.modele)
    return {"modele": payload.modele, "reponse": resultat}

@app.post("/comparer")
async def comparer(payload: ComparaisonRequest):
    prompt = prompt_comparer(payload.code_source, payload.texte_llama, payload.texte_gemma)
    resultat_brut = appeler_ollama(prompt,payload.modele_juge,timeout=360,num_ctx=8192,format_json=True)
 
    resultat_parse = extraire_json(resultat_brut)
 
    if resultat_parse is not None:
        return {"modele_juge": payload.modele_juge, "comparaison": resultat_parse}
 
    # Le modele n'a pas produit un JSON valide : on renvoie le texte brut en secours
    return {"modele_juge": payload.modele_juge, "comparaison": resultat_brut, "erreur_parsing": True}

@app.post("/comparer-prompts")
async def comparer_prompts(payload: ComparaisonPromptRequest):
    prompt = prompt_comparer_prompts(payload.prompt_a, payload.prompt_b)
    resultat_brut = appeler_ollama(
        prompt, payload.modele_juge, timeout=180, num_ctx=6144, format_json=True
    )

    resultat_parse = extraire_json(resultat_brut)

    if resultat_parse is not None:
        return {"modele_juge": payload.modele_juge, "resultat": resultat_parse}

    return {"modele_juge": payload.modele_juge, "resultat": resultat_brut, "erreur_parsing": True}

@app.post("/classifier-prompt")
async def classifier_prompt(payload: ClassificationPromptRequest):

    prompt = prompt_classifier(payload.prompt, payload.contexte_prompts)

    resultat_brut = appeler_ollama(
        prompt,
        payload.modele_juge,
        timeout=180,
        num_ctx=4096,
        format_json=True,
    )

    resultat_parse = extraire_json(resultat_brut)

    if resultat_parse is not None:
        return {
            "modele_juge": payload.modele_juge,
            "classification": resultat_parse,
        }

    return {
        "modele_juge": payload.modele_juge,
        "classification": resultat_brut,
        "erreur_parsing": True,
    }

@app.get("/prompts")
def page_prompts():
    return FileResponse(str(BASE_DIR / "static" / "prompts.html"))

@app.post("/activer-prompt")
async def activer_prompt(payload: ActiverPromptRequest):

    if payload.tache not in TACHES_VALIDES:
        raise HTTPException(
            status_code=400,
            detail=f"Tache invalide. Valeurs possibles : {', '.join(TACHES_VALIDES)}",
        )

    PROMPTS_ACTIFS[payload.tache] = payload.prompt_template

    # suppression du prompt temporaire
    PROMPTS_TEST.pop(payload.tache, None)

    return {
        "message": f"Prompt activé pour la tâche '{payload.tache}'.",
        "tache": payload.tache,
    }
@app.post("/tester-prompt")
async def tester_prompt(payload: ActiverPromptRequest):

    if payload.tache not in TACHES_VALIDES:
        raise HTTPException(
            status_code=400,
            detail=f"Tache invalide. Valeurs possibles : {', '.join(TACHES_VALIDES)}",
        )

    PROMPTS_TEST[payload.tache] = payload.prompt_template

    return {
        "message": "Prompt temporaire prêt pour le test.",
        "tache": payload.tache,
        "mode": "test"
    }

@app.post("/restaurer-prompt")
async def restaurer_prompt(payload: RestaurerPromptRequest):
    if payload.tache not in TACHES_VALIDES:
        raise HTTPException(
            status_code=400,
            detail=f"Tache invalide. Valeurs possibles : {', '.join(TACHES_VALIDES)}",
        )

    PROMPTS_ACTIFS.pop(payload.tache, None)

    return {
        "message": f"Le prompt par défaut est réactivé pour '{payload.tache}'.",
        "tache": payload.tache,
    }
@app.get("/etat-prompts")
def etat_prompts():
    return {
        tache: {
            "personnalise": tache in PROMPTS_ACTIFS
        }
        for tache in TACHES_VALIDES
    }

@app.post("/annuler-test-prompt")
async def annuler_test_prompt(payload: RestaurerPromptRequest):

    PROMPTS_TEST.pop(payload.tache, None)

    return {
        "message": f"Test annulé pour '{payload.tache}'. Retour au prompt normal.",
        "tache": payload.tache
    }
@app.get("/etat-test-prompt")
def etat_test_prompt():

    return {
        "test_actif": len(PROMPTS_TEST) > 0,
        "taches": list(PROMPTS_TEST.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)