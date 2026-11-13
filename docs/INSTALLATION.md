# Installation — BETPREDICT AI

## Prérequis

- Docker & Docker Compose **ou**
- Python 3.12+, Node.js 20+, PostgreSQL 16, Redis 7

## Démarrage rapide (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Services :

| Service   | URL                      |
|-----------|--------------------------|
| Frontend  | http://localhost:3000    |
| API       | http://localhost:8000    |
| OpenAPI   | http://localhost:8000/docs |
| Health    | http://localhost:8000/health |

Au premier démarrage, le backend exécute les migrations Alembic et le seed **DEMO**.

### Comptes démo

| Email | Mot de passe | Rôle |
|-------|--------------|------|
| `user@betpredict.ai` | `User123!` | Free |
| `premium@betpredict.ai` | `Premium123!` | Premium |
| `admin@betpredict.ai` | `Admin123!` | Admin (MFA `000000`) |

## Mode démonstration

`DEMO_MODE=true` (défaut) active des données sportives **synthétiques clairement étiquetées**.

Pour utiliser une API licenciée :

1. Renseigner la clé (`API_FOOTBALL_KEY`, `SPORTMONKS_TOKEN` ou `FOOTBALL_DATA_ORG_KEY`)
2. Définir `PRIMARY_DATA_PROVIDER` (`api_football` | `sportmonks` | `football_data_org`)
3. Mettre `DEMO_MODE=false`

Sans clé valide, l'application reste en mode démo.

## Développement local (sans Docker pour le frontend/backend)

```bash
# Infra
docker compose up -d db redis

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' ../.env | xargs)
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. pytest -q
```

## Conformité

- Service d'**analyse et d'information** uniquement
- Aucune mise acceptée, aucun fonds joueur conservé
- Vérification d'âge légal à l'inscription
- Outils de pause / auto-exclusion
- Pas de stratégie de récupération automatique des pertes
