Readme · MD
# Foody — Tendances culinaires par ville
 
Pipeline de données automatisé qui suit quotidiennement l'intérêt de recherche pour différents types de cuisine (pizza, sushi, kebab, restaurant italien, etc.) dans les grandes villes françaises, via Google Trends, et l'expose dans une web app.
 
![Pipeline Status](https://github.com/EDSIOT/foody/actions/workflows/daily_pipeline.yml/badge.svg)
 
## Sommaire
 
- [Objectif](#objectif)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Choix méthodologiques et limites](#choix-méthodologiques-et-limites)
- [Installation et lancement local](#installation-et-lancement-local)
- [Structure du projet](#structure-du-projet)
- [Automatisation](#automatisation)
- [Tests](#tests)
- [Pistes d'amélioration](#pistes-damélioration)
## Objectif
 
Répondre à une question simple : **quels types de cuisine intéressent le plus les internautes, ville par ville, et comment cet intérêt évolue dans le temps ?**
 
Le projet illustre un pipeline de données de bout en bout — ingestion, nettoyage, normalisation, stockage, exposition via API, visualisation — construit et documenté avec une attention particulière portée à la robustesse (gestion des erreurs, rate limiting, retries) et à la traçabilité méthodologique des données.
 
## Architecture
 
```
┌────────────────────────────┐
│   Google Trends            │   (via pytrends, non officiel)
│   interest_by_region       │
└──────────┬─────────────────┘
           │  cron quotidien (GitHub Actions)
           ▼
┌────────────────────────────┐
│  run_pipeline.py           │
│  - ingestion par lots      │
│  - retry / backoff         │
│  - normalisation par ancre │
└──────────┬─────────────────┘
           ▼
┌────────────────────────────┐
│  PostgreSQL (Supabase)     │
│  table raw_cuisine_trends  │
└──────────┬─────────────────┘
           ▼
┌────────────────────────────┐
│  API FastAPI               │
│  /cuisines, /cuisines/top  │
│  /cities                   │
└──────────┬─────────────────┘
           ▼
┌────────────────────────────┐
│  Frontend Nuxt/Vue         │
│  tableau, carte, graphiques│
└────────────────────────────┘
```
 
## Stack technique
 
| Couche | Technologie | Justification |
|---|---|---|
| Ingestion | Python, `pytrends` | Seule librairie accessible gratuitement pour Google Trends (l'API officielle est en alpha fermée, les API tierces payantes ont été écartées pour raisons de coût) |
| Gestion des dépendances | `uv` | Gestion moderne et rapide des environnements et des lockfiles |
| Base de données | PostgreSQL (Supabase) | Base relationnelle managée gratuite, adaptée à des séries temporelles |
| API interne | FastAPI | Typage natif, documentation Swagger auto-générée, tests faciles |
| Frontend | Nuxt / Vue.js | Framework demandé par les offres visées, SSR natif |
| Orchestration | GitHub Actions (cron) | Gratuit, pas d'infrastructure à maintenir, logs et statut visibles publiquement |
 
## Choix méthodologiques et limites
 
Cette section documente honnêtement les contraintes et arbitrages faits, plutôt que de les dissimuler.
 
### 1. `pytrends` est une librairie non officielle et non maintenue
 
Le projet dépend d'endpoints internes de Google Trends via `pytrends`, une librairie **archivée depuis avril 2025**. Conséquences directes gérées dans le code :
- Rate limiting fréquent (erreurs HTTP 429), géré par un système de retry avec backoff exponentiel et pauses aléatoires (jitter) entre les lots.
- Certains endpoints (`trending_searches`) se sont révélés cassés (404) en cours de développement et ont été abandonnés au profit de `interest_by_region`, plus stable.
- Le pipeline est conçu pour **tolérer l'échec partiel** : si un lot de requêtes échoue après plusieurs tentatives, le pipeline continue avec les données disponibles plutôt que d'échouer entièrement.
### 2. Limite du nombre de mots-clés par requête (5 max)
 
Google Trends limite chaque appel à 5 mots-clés simultanés. Le projet suit 23 catégories de cuisine, réparties en **lots de 5**, avec le mot-clé "Pizza" inclus systématiquement dans chaque lot comme **ancre de normalisation**.
 
### 3. Normalisation par ancre commune
 
Les scores Google Trends sont des **indices relatifs de 0 à 100**, normalisés indépendamment à l'intérieur de chaque appel — deux appels séparés ne sont **pas comparables directement**. Pour rendre les 23 cuisines comparables entre elles malgré la limite de 5 mots-clés par appel :
- "Pizza" est inclus dans chaque lot.
- Le score moyen de "Pizza" dans le premier lot sert de référence.
- Un facteur de correction est calculé pour chaque lot suivant (`ancre_référence / ancre_lot`) et appliqué à toutes les autres valeurs du lot.
**Limite assumée** : cette technique introduit une marge d'erreur (imprécision d'arrondi de Google, effet de plafond si l'ancre atteint 100 dans un lot). Les scores obtenus sont donc des **indices relatifs approximatifs**, pas des volumes de recherche absolus. Chaque ligne en base est marquée `is_normalized` et `anchor_used` pour garder cette traçabilité.
 
### 4. Topics vs mots-clés textuels
 
Quand c'était possible, les cuisines sont suivies via leur **Topic** Google (identifiant sémantique du type `/m/xxxx` ou `/g/xxxx`), qui regroupe les variantes linguistiques et synonymes — plutôt qu'un simple mot-clé textuel, qui aurait biaisé les résultats vers les recherches en français uniquement. Pour certains termes sans Topic clairement identifié, un mot-clé textuel brut a été conservé en fallback (voir `CUISINE_TOPICS` dans `ingestion/fetch_trends.py` pour le détail).
 
### 5. Biais de la source
 
- Google Trends mesure un **volume de recherche**, pas une fréquentation réelle de restaurants — une cuisine peut être très recherchée sans que l'offre de restaurants correspondante soit dense localement, et inversement.
- La couverture par ville dépend du volume minimum de recherches nécessaire pour que Google publie une donnée (`inc_low_vol=True` utilisé pour limiter la perte de données, mais les très petites villes restent sous-représentées).
## Installation et lancement local
 
### Prérequis
- Python 3.12+ et [`uv`](https://docs.astral.sh/uv/)
- Node.js 18+
- Un projet [Supabase](https://supabase.com) (gratuit)
### Backend / pipeline
 
```bash
git clone https://github.com/EDSIOT/foody.git
cd foody
uv sync
```
 
Créer un fichier `.env` à la racine (voir `.env.example`) :
```
DATABASE_URL=postgresql://postgres:[MOT-DE-PASSE]@db.xxxxx.supabase.co:6543/postgres
```
 
Lancer le pipeline manuellement :
```bash
uv run python run_pipeline.py
```
 
Lancer l'API :
```bash
uv run uvicorn api.main:app --reload
```
Documentation interactive disponible sur `http://localhost:8000/docs`.
 
### Frontend
 
```bash
cd frontend
npm install
```
 
Créer un `.env` dans `frontend/` :
```
NUXT_PUBLIC_API_BASE=http://localhost:8000
```
 
```bash
npm run dev
```
Application disponible sur `http://localhost:3000`.
 
## Structure du projet
 
```
foody/
├── ingestion/
│   ├── fetch_trends.py       # logique pytrends : lots, retry, normalisation
│   └── db.py                  # connexion et insertion PostgreSQL
├── api/
│   ├── main.py                 # point d'entrée FastAPI
│   ├── routes.py               # endpoints /cuisines, /cities...
│   └── test_routes.py          # tests unitaires pytest
├── frontend/
│   ├── pages/                  # pages Nuxt
│   ├── components/             # carte, graphiques
│   └── composables/useApi.js   # appels vers l'API
├── run_pipeline.py             # orchestrateur du pipeline complet
├── .github/workflows/
│   └── daily_pipeline.yml      # automatisation quotidienne
├── logs/                       # logs d'exécution horodatés
└── .env.example
```
 
## Automatisation
 
Le pipeline s'exécute automatiquement chaque jour via **GitHub Actions** (cron), sans serveur dédié :
- Déclenchement quotidien programmé + déclenchement manuel possible (`workflow_dispatch`).
- Logs uploadés en artifact en cas d'échec pour faciliter le diagnostic à distance.
- Utilisation des identifiants de connexion via GitHub Secrets (`DATABASE_URL`), jamais en clair dans le dépôt.
## Tests
 
```bash
uv run pytest
```
 
Couvre les endpoints principaux de l'API (statut, filtrage par ville, format de réponse).
 
## Pistes d'amélioration
 
- Ajout de tests end-to-end (Playwright) sur le parcours utilisateur du frontend.
- Carte interactive (Leaflet) avec code couleur par cuisine dominante.
- Graphiques d'évolution temporelle une fois plusieurs semaines de données accumulées.
- Détection des pics ponctuels (ex: ouverture d'un restaurant très médiatisé) via `related_topics()`.
- Déploiement public (API sur Render/Railway, frontend sur Vercel) avec lien démo live.
- Déduplication ou contrainte d'unicité en base pour éviter les insertions redondantes en cas de relance manuelle du pipeline le même jour.
 
