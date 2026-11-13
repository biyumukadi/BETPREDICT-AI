# BETPREDICT AI

Plateforme professionnelle d'analyses et de pronostics football basés sur des **probabilités statistiques calibrées**.

> Service d'information uniquement — aucune mise n'est acceptée, aucun résultat n'est garanti.

## Fonctionnalités MVP

- Dashboard matchs (aujourd'hui / demain / 7 jours / terminés)
- Moteur IA ensemble : Poisson, Elo, régression logistique, XGBoost, Monte-Carlo
- Fiche match détaillée (marchés, facteurs, incertitudes, value bets théoriques)
- Historique & métriques (hit-rate, Brier, Log Loss) — suppression sélective interdite
- Budget responsable (limites, ROI, pause / auto-exclusion)
- Abonnements Free / Premium / Pro (Stripe + hooks Mobile Money)
- Admin (users, sync, audit, sources de données)
- Multilingue FR / EN, thème clair / sombre, PWA
- Mode **DEMO** explicite sans clé API

## Stack

| Couche | Techno |
|--------|--------|
| Frontend | Next.js, TypeScript, Tailwind, Recharts |
| Backend | FastAPI, SQLAlchemy, Alembic, Celery |
| Data | PostgreSQL, Redis |
| IA | NumPy, SciPy, scikit-learn, XGBoost |
| Providers | API-Football, Sportmonks, football-data.org, Demo |

## Démarrage

```bash
cp .env.example .env
docker compose up --build
```

- App : http://localhost:3000  
- API docs : http://localhost:8000/docs  

Documentation : [docs/INSTALLATION.md](docs/INSTALLATION.md) · [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Comptes démo

- `user@betpredict.ai` / `User123!`
- `premium@betpredict.ai` / `Premium123!`
- `admin@betpredict.ai` / `Admin123!` (MFA `000000`)

## Tests

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

## Architecture

```
frontend/          Next.js PWA
backend/app/
  api/routes/      Auth, fixtures, predictions, budget, billing, admin
  services/
    prediction/    Ensemble IA
    data_providers/ Adaptateurs interchangeables
    odds/          EV & marges bookmakers
  models/          PostgreSQL ORM
  db/seed.py       Données DEMO étiquetées
```

## Licence & conformité

Respectez la législation applicable aux services liés aux paris et à la publicité dans votre juridiction. Les cotes ne s'affichent que depuis des sources autorisées / licenciées lorsqu'elles sont configurées.
