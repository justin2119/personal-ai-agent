# Personal AI Agent avec Tool Calling

> Agent conversationnel autonome, doté de capacités de Tool Calling dynamique, développé dans le cadre du **Bootcamp RodiumAI**.

| | |
|---|---|
| **Projet** | Personal AI Agent avec Tool Calling (RodiumAI Bootcamp) |
| **Auteur** | Justin BINA (BINA TOYI) |
| **Structure** | ErreurZéro / B-SOLUTIONS |
| **Mentor / Formateur** | Omar Farouk KOUGBADA |
| **Statut** | En développement |

---

## Sommaire

1. [Présentation](#présentation)
2. [Fonctionnalités](#fonctionnalités)
3. [Architecture](#architecture)
4. [Stack technique](#stack-technique)
5. [Outils intégrés](#outils-intégrés)
6. [Prérequis](#prérequis)
7. [Installation et configuration](#installation-et-configuration)
8. [Lancement](#lancement)
9. [Flux OAuth Google](#flux-oauth-google)
10. [Structure du repository](#structure-du-repository)
11. [Cas de test et démonstration](#cas-de-test-et-démonstration)
12. [Sécurité](#sécurité)
13. [Gestion des erreurs](#gestion-des-erreurs)
14. [Déploiement](#déploiement)
15. [Licence et crédits](#licence-et-crédits)

---

## Présentation

Le **Personal AI Agent** est un assistant conversationnel personnel qui ne se contente pas de répondre à des questions : il raisonne, choisit l'outil approprié et l'exécute pour accomplir une tâche concrète (consulter la météo, rechercher sur le web, gérer son agenda, retrouver un document, envoyer un e-mail ou créer une note).

Le modèle de langage est servi par l'endpoint **RodiumAI** (modèle `openai/gpt-6.1-sol`). La logique d'agent repose sur **PydanticAI**, exposée via une API **FastAPI**, et consommée par une interface web légère en **HTML5, CSS3 et JavaScript (ES6+)**.

## Fonctionnalités

- **Agent conversationnel autonome** avec Tool Calling dynamique : l'agent décide seul quand et quel outil invoquer, puis synthétise la réponse.
- **Sessions multiples** : plusieurs conversations indépendantes, accessibles depuis l'interface.
- **Persistance locale** : l'historique des sessions est conservé dans le `localStorage` du navigateur.
- **Confirmation explicite des actions sensibles** : l'envoi d'e-mail via SMTP ne s'exécute jamais sans validation préalable de l'utilisateur.
- **Résilience** : gestion robuste des erreurs et fallbacks, avec l'objectif explicite de ne jamais renvoyer d'erreur 500 à l'interface.
- **Interface soignée** : design sobre, identité visuelle RodiumAI (couleur principale `#0066CC`), icônes Lucide.

## Architecture

```
+---------------------------+          HTTP / JSON          +-----------------------------+
|  Frontend (navigateur)    | -----------------------------> |  Backend FastAPI (uvicorn)  |
|  HTML5 / CSS3 / ES6+      |                                |  app/main.py                |
|  Lucide Icons             | <----------------------------- |  PydanticAI Agent           |
|  localStorage (sessions)  |                                |  app/agent.py               |
+---------------------------+                                +--------------+--------------+
                                                                           |
                          +------------------------------------------------+------------------+
                          |                    |                 |            |             |        |
                  RodiumAI LLM        OpenWeatherMap      Tavily    Google API     SMTP     Notion API
                (openai/gpt-6.1-sol)   (météo)        (recherche) (Calendar/Drive)  (e-mail)   (pages)
```

Flux d'une requête :

1. L'utilisateur envoie un message depuis l'interface (session courante).
2. Le frontend transmet l'historique utile au backend.
3. L'agent PydanticAI interroge le LLM RodiumAI, qui peut demander l'exécution d'un ou plusieurs outils.
4. Chaque outil est appelé ; en cas d'échec, un message d'erreur structuré est renvoyé à l'agent, qui adapte sa réponse.
5. La réponse finale est renvoyée au frontend et enregistrée dans la session locale.

## Stack technique

### Backend

| Composant | Technologie |
|---|---|
| Framework API | FastAPI |
| Serveur ASGI | Uvicorn |
| Agent / Tool Calling | PydanticAI |
| LLM | RodiumAI, modèle `openai/gpt-6.1-sol` |
| Gestionnaire de paquets | `uv` (Astral) |
| Intégrations Google | google-api-python-client, google-auth, google-auth-oauthlib |
| Recherche web | tavily-python |
| Client HTTP | httpx |
| Configuration | python-dotenv |

### Frontend

| Composant | Technologie |
|---|---|
| Structure | HTML5 sémantique |
| Style | CSS3 (style carré : rayons de bordure de 4 à 5 px, couleur de marque `#0066CC`) |
| Logique | JavaScript ES6+ (sans framework) |
| Icônes | Lucide Icons |
| Persistance | `localStorage` |

## Outils intégrés

| # | Outil | Description | Points notables |
|---|---|---|---|
| 1 | **Météo** | Conditions météorologiques via l'API OpenWeatherMap | Fallback et gestion d'erreurs explicite |
| 2 | **Recherche web** | Recherche d'informations actualisées via Tavily | Résultats synthétisés par l'agent |
| 3 | **Google Calendar** | Lister les événements et créer un événement | Authentification OAuth2 (token) |
| 4 | **Google Drive** | Rechercher des fichiers | Authentification OAuth2 (token) |
| 5 | **E-mail (SMTP)** | Envoi d'e-mails sécurisé | Confirmation explicite obligatoire avant envoi |
| 6 | **Notion** | Création et recherche de notes / pages via l'API Notion | Clé d'intégration Notion requise |

## Prérequis

- **Python 3.11** ou supérieur
- **uv** (gestionnaire de paquets et d'environnements Astral) : https://docs.astral.sh/uv/
- Un navigateur moderne (Chrome, Firefox, Edge, Safari)
- Un serveur statique pour le frontend (Live Server de VS Code, `python -m http.server`, ou équivalent)
- Les clés d'API nécessaires aux outils que vous souhaitez activer (voir ci-dessous)

## Installation et configuration

### 1. Cloner le repository

```bash
git clone https://github.com/justin2119/personal-ai-agent.git
cd personal-ai-agent
```

### 2. Installer les dépendances backend

```bash
cd backend
uv sync
```

Les dépendances sont déclarées dans `backend/requirements.txt` (FastAPI, Uvicorn, PydanticAI, OpenAI, httpx, python-dotenv, google-api-python-client, google-auth, google-auth-oauthlib, tavily-python).

### 3. Configurer les variables d'environnement

Copier le modèle et le compléter :

```bash
cp .env.example .env
```

Exemple complet de fichier `backend/.env` :

```dotenv
# --- LLM RodiumAI ---
RODIUM_API_KEY=your_rodium_api_key
RODIUM_BASE_URL=https://api.rodiumai.io/v1

# --- Recherche web (Tavily) ---
TAVILY_API_KEY=your_tavily_api_key

# --- Météo (OpenWeatherMap) ---
WEATHER_API_KEY=your_openweathermap_api_key

# --- Notion ---
NOTION_API_KEY=your_notion_integration_secret

# --- E-mail (SMTP) ---
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_smtp_password_or_app_password

# --- Google (Calendar / Drive) ---
GOOGLE_TOKEN_FILE=token.json
GOOGLE_CALENDAR_ID=primary
```

| Variable | Obligatoire | Description |
|---|---|---|
| `RODIUM_API_KEY` | Oui | Clé d'API RodiumAI pour le LLM |
| `RODIUM_BASE_URL` | Oui | URL de base de l'API RodiumAI (`https://api.rodiumai.io/v1`) |
| `TAVILY_API_KEY` | Pour la recherche web | Clé d'API Tavily |
| `WEATHER_API_KEY` | Pour la météo | Clé d'API OpenWeatherMap |
| `NOTION_API_KEY` | Pour Notion | Secret de l'intégration Notion (à partager avec les pages ciblées) |
| `SMTP_HOST` | Pour l'e-mail | Serveur SMTP sortant |
| `SMTP_PORT` | Pour l'e-mail | Port SMTP (587 pour STARTTLS par défaut) |
| `SMTP_USER` | Pour l'e-mail | Identifiant du compte expéditeur |
| `SMTP_PASSWORD` | Pour l'e-mail | Mot de passe ou mot de passe d'application |
| `GOOGLE_TOKEN_FILE` | Pour Google | Chemin du fichier `token.json` (défaut : `token.json`) |
| `GOOGLE_CALENDAR_ID` | Non | Agenda ciblé (défaut : `primary`) |

> Ne jamais committer le fichier `.env`, `token.json` ni `credentials.json`. Vérifier que ces fichiers figurent bien dans `.gitignore`.

## Lancement

### Backend

Depuis le dossier `backend/` :

```bash
uv run uvicorn app.main:app --reload
```

L'API est alors disponible sur `http://127.0.0.1:8000`. Le endpoint de santé `/health` permet de vérifier que le service répond.

En production, le `Procfile` lance l'application sans rechargement automatique :

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Frontend

Le frontend est constitué de fichiers statiques (`index.html`, `style.css`, `app.js`). Deux options :

- **Live Server** (extension VS Code) : ouvrir `frontend/index.html` puis « Open with Live Server ».
- **Serveur statique Python** :

```bash
cd frontend
python -m http.server 5500
```

Puis ouvrir `http://127.0.0.1:5500`.

Vérifier que l'URL du backend configurée dans `app.js` correspond à l'adresse de l'API (par défaut `http://127.0.0.1:8000`).

## Flux OAuth Google

L'intégration Google Calendar et Google Drive utilise OAuth2 avec deux fichiers :

| Fichier | Rôle | Origine |
|---|---|---|
| `credentials.json` | Identifiants client OAuth de l'application | Google Cloud Console |
| `token.json` | Jeton d'accès et de rafraîchissement de l'utilisateur | Généré lors de la première autorisation |

Étapes de mise en place :

1. Créer un projet dans la **Google Cloud Console**.
2. Activer les API **Google Calendar API** et **Google Drive API**.
3. Configurer l'**écran de consentement OAuth** (type Externe, ajouter l'adresse e-mail de test).
4. Créer des identifiants de type **ID client OAuth** (application de bureau), puis télécharger le JSON.
5. Renommer le fichier téléchargé en `credentials.json` et le placer dans `backend/`.
6. Lancer le flux d'autorisation : à la première utilisation, le navigateur s'ouvre pour consentir aux portées demandées ; un fichier `token.json` est alors créé à l'emplacement défini par `GOOGLE_TOKEN_FILE`.
7. Les exécutions suivantes réutilisent `token.json` et le rafraîchissent automatiquement.

En cas d'expiration ou de révocation du jeton, supprimer `token.json` et relancer le flux d'autorisation.

## Structure du repository

```
personal-ai-agent/
├── README.md
├── render.yaml                 # Blueprint de déploiement Render (backend Docker)
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # Point d'entrée FastAPI (routes, /health)
│   │   ├── agent.py            # Agent PydanticAI et orchestration du Tool Calling
│   │   ├── config.py           # Chargement et validation de la configuration
│   │   └── tools/              # Outils : météo, Tavily, Google, SMTP, Notion
│   ├── test_agent.py           # Tests de l'agent
│   ├── requirements.txt        # Dépendances Python
│   ├── .env.example            # Modèle de variables d'environnement
│   ├── Dockerfile              # Image de conteneur du backend
│   ├── .dockerignore
│   └── Procfile                # Commande de lancement (PaaS)
└── frontend/
    ├── index.html              # Structure de l'interface
    ├── style.css               # Feuille de style (style carré, charte RodiumAI)
    ├── app.js                  # Logique client : sessions, appels API, localStorage
    └── netlify.toml            # Configuration de déploiement Netlify
```

## Cas de test et démonstration

Le fichier `backend/test_agent.py` regroupe les tests de l'agent. Les scénarios suivants permettent de valider manuellement chaque outil depuis l'interface.

| Scénario | Requête type | Résultat attendu |
|---|---|---|
| Météo | « Quel temps fait-il à Lomé aujourd'hui ? » | Appel de l'outil météo, réponse avec température et conditions |
| Météo (erreur) | Ville inexistante ou clé invalide | Message d'erreur explicite, aucune erreur 500 |
| Recherche web | « Quelles sont les dernières actualités sur l'IA ? » | Appel de Tavily, réponse sourcée |
| Agenda : lecture | « Quels sont mes rendez-vous de demain ? » | Liste des événements Google Calendar |
| Agenda : création | « Crée un rendez-vous demain à 10 h intitulé Réunion projet » | Création de l'événement après OAuth2 |
| Drive | « Retrouve mon document Rapport final » | Liste des fichiers correspondants |
| E-mail | « Envoie un e-mail à X avec le sujet Y » | Demande de confirmation explicite, envoi uniquement après validation |
| Notion | « Crée une note intitulée Idées de la semaine » | Page créée dans Notion |
| Session | Création d'une nouvelle session puis rechargement de la page | Sessions et messages restaurés depuis le `localStorage` |

## Sécurité

- **Secrets** : toutes les clés sont lues depuis l'environnement ; aucune clé n'est codée en dur. Les fichiers `.env`, `token.json` et `credentials.json` sont exclus du versionnement.
- **Actions sensibles** : l'envoi d'e-mail est soumis à une confirmation explicite de l'utilisateur avant toute exécution.
- **Principe du moindre privilège** : limiter les portées OAuth Google à l'usage nécessaire, et partager la page Notion ciblée uniquement avec l'intégration.
- **Conteneur** : l'image Docker est construite à partir du dossier `backend/` avec un `.dockerignore` pour éviter d'embarquer des fichiers sensibles.

## Gestion des erreurs

L'agent est conçu pour rester disponible même lorsqu'un service externe échoue :

- Chaque outil capture ses exceptions et renvoie un résultat d'erreur structuré à l'agent, qui formule une réponse compréhensible pour l'utilisateur.
- La météo dispose d'un mécanisme de fallback en cas d'indisponibilité du fournisseur principal.
- Les erreurs de configuration (clé absente, service non connecté) sont signalées clairement sans interrompre le serveur.
- Objectif : aucune réponse HTTP 500 exposée au frontend.

## Déploiement

Le fichier `render.yaml` décrit un service web **Render** de type Docker, situé dans `backend/`, avec :

- un contrôle de santé sur `/health` ;
- le déploiement automatique à chaque push (`autoDeploy: true`) ;
- les variables d'environnement sensibles à renseigner dans le tableau de bord Render (`sync: false`).

Le frontend peut être publié sur **Netlify** grâce à `frontend/netlify.toml`. Penser à mettre à jour l'URL du backend dans `app.js` après déploiement.

## Licence et crédits

Projet réalisé dans le cadre du **Bootcamp RodiumAI**.

- **Auteur** : Justin BINA (BINA TOYI), ErreurZéro / B-SOLUTIONS
- **Mentor / Formateur** : Omar Farouk KOUGBADA

Licence : à préciser par l'auteur.
