# 🤖 Code Review AI

> Assistant IA local de revue de code source — 100% hors-ligne, zéro fuite de données.

Analysez vos fichiers de code avec des modèles de langage open-source (LLMs) exécutés **entièrement en local** via [Ollama](https://ollama.com). Aucune donnée ne quitte votre machine.

---

## ✨ Fonctionnalités

| Fonctionnalité | Endpoint | Description |
|---|---|---|
| **Explication** | `POST /expliquer` | Explication claire de la logique du code, des fonctions et de l'objectif global |
| **Mauvaises pratiques** | `POST /mauvaises-pratiques` | Détection des failles de sécurité, conventions de nommage, complexité algorithmique |
| **Améliorations** | `POST /ameliorations` | Suggestions de refactoring concrètes avec justifications |
| **Résumé** | `POST /resume` | Synthèse courte (4-6 lignes) : rôle, points forts, faiblesses |
| **Comparaison LLM-Juge** | `POST /comparer` | Arbitrage factuel entre deux analyses par un modèle tiers (Qwen 2.5) |
| **Labo de prompts** | `POST /comparer-prompts` | Test A/B de deux versions de prompts |
| **Classification** | `POST /classifier-prompt` | Identification automatique de l'intention d'un prompt |
| **Gestion des prompts** | `POST /activer-prompt` | Personnalisation et restauration dynamique des templates |

---

## 🏗️ Architecture

```
code-review-ai/
├── main.py                  # Backend FastAPI — API REST + prompts + endpoints
├── database.py              # Connexion MySQL + gestion de la table users
├── init_db.py               # Script d'initialisation de la base de données
├── comparatif.py            # Script de benchmark automatisé (Llama 3.2 vs Gemma 2)
├── requirements.txt         # Dépendances Python
├── resultats_comparatif.json  # Résultats bruts du benchmark (généré)
├── static/
│   ├── index.html           # Interface principale
│   ├── login.html           # Page de connexion
│   ├── prompts.html         # Laboratoire d'ingénierie de prompts
│   ├── styles.css           # Design système (CSS custom)
│   ├── app.js               # Logique frontend principale
│   ├── login.js             # Logique d'authentification
│   ├── prompts.js           # Logique du labo de prompts
│   └── favicon.svg          # Icône du site
└── exemples/                # Fichiers de test avec défauts volontaires
    ├── calculatrice.py
    ├── Gestion utilisateurs .py
    ├── Traitement donnees.py
    ├── gestion_commandes.py
    ├── parseur_fichier.py
    └── test.js
```

---

## 🚀 Installation

### Prérequis

- **Python** 3.10+
- **MySQL** 8.0+ (ou XAMPP / MariaDB)
- **Ollama** — [ollama.com](https://ollama.com)

### 1. Cloner le projet

```bash
git clone <repository_url>
cd code-review-ai
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Télécharger les modèles Ollama

```bash
ollama pull llama3.2
ollama pull gemma2
ollama pull qwen2.5
```

### 4. Configurer la base de données (optionnel)

Par défaut, l'application se connecte à MySQL sur `127.0.0.1:3306` avec l'utilisateur `root`. Vous pouvez adapter via des variables d'environnement :

```bash
set DB_HOST=127.0.0.1
set DB_PORT=3306
set DB_USER=root
set DB_PASSWORD=votre_mot_de_passe
set DB_NAME=code_review_ai
```

### 5. Initialiser la base de données

```bash
python init_db.py
```

### 6. Lancer l'application

```bash
python main.py
```

L'application démarre sur **http://localhost:8000**. Si Ollama n'est pas actif, FastAPI tentera de le démarrer automatiquement.

---

## 💻 Utilisation

### Interface Web

| Page | URL |
|---|---|
| Accueil (analyse de code) | http://localhost:8000 |
| Connexion | http://localhost:8000/login |
| Laboratoire de prompts | http://localhost:8000/prompts |

1. Choisissez une tâche d'analyse (`Expliquer`, `Mauvaises pratiques`, `Améliorations`, `Résumé`).
2. Sélectionnez le modèle IA (`llama3.2` ou `gemma2`).
3. Collez votre code ou téléchargez un fichier source.
4. Consultez l'analyse générée.

### API REST (exemples cURL)

```bash
# Analyser les mauvaises pratiques d'un fichier
curl -X POST http://localhost:8000/mauvaises-pratiques \
  -F "fichier=@mon_script.py" \
  -F "modele=gemma2"

# Comparer deux analyses avec le LLM-Juge
curl -X POST http://localhost:8000/comparer \
  -H "Content-Type: application/json" \
  -d '{"code_source": "...", "texte_llama": "...", "texte_gemma": "..."}'
```

---

## 📊 Benchmark : Llama 3.2 vs Gemma 2

Un script de benchmark automatisé (`comparatif.py`) a été utilisé pour comparer les deux modèles sur 24 appels (3 fichiers × 2 modèles × 4 tâches).

```bash
python comparatif.py
```

Les résultats sont sauvegardés dans `resultats_comparatif.json`.

### Résultats clés

| Critère | Llama 3.2 (3B) | Gemma 2 (9B) |
|---|---|---|
| Détection failles de sécurité | Correcte mais timide | **Claire et appropriée** |
| Cohérence inter-endpoints | Incohérences observées | **Cohérent** |
| Hallucinations | Présentes | Présentes, moins fréquentes |
| Structure des réponses | Parfois confuse | **Concise et structurée** |
| Temps moyen par requête | **21,45 s** | 82,99 s |
| Consommation RAM | **~4-6 GB** | ~8-10 GB |

> **Conclusion** : Gemma 2 produit des analyses plus fiables et mieux structurées. Llama 3.2 est préférable si la rapidité ou les ressources limitées sont la priorité. Les deux modèles doivent être vus comme des **assistants de première analyse**, à compléter par une revue humaine.

---

## 🛠️ Stack technique

| Composant | Technologie |
|---|---|
| Backend API | Python 3.10+ / FastAPI / Uvicorn |
| Base de données | MySQL / PyMySQL |
| Moteur IA | Ollama (local) — Llama 3.2, Gemma 2, Qwen 2.5 |
| Authentification | Bcrypt (hachage salé) |
| Frontend | HTML5 / CSS3 / JavaScript ES6+ (Vanilla) |

---

## 🔒 Sécurité

- **Exécution 100% locale** — Aucune donnée envoyée vers le cloud.
- **Mots de passe hachés** avec bcrypt (jamais stockés en clair).
- **Requêtes SQL paramétrées** pour prévenir les injections.

---

## 📄 Licence

Projet réalisé dans le cadre d'un stage.
