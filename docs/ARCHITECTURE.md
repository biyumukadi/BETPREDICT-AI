# Architecture — BETPREDICT AI

## Vue d'ensemble

```
┌─────────────┐     REST/JSON      ┌──────────────┐
│  Next.js    │ ◄────────────────► │   FastAPI    │
│  PWA FR/EN  │                    │  OpenAPI     │
└─────────────┘                    └──────┬───────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              PostgreSQL               Redis               Celery Beat
              (domain + IA)         (cache/queue)        (sync/eval)
                                          │
                                          ▼
                               Sports Data Adapters
                     demo | api_football | sportmonks | football-data.org
```

## Moteur de prédiction

Pipeline ensemble (pas de fuite future : features `as_of_date` ≤ kickoff) :

1. **Poisson** — lambdas attaque/défense, scorelines, O/U, BTTS
2. **Elo** — force relative + avantage domicile
3. **Logistic** — features (forme, xG, repos, blessures)
4. **XGBoost** — classification 1X2
5. **Monte-Carlo** — distributions empiriques
6. **Calibration** — pondération + temperature scaling + indice de confiance plafonné

## Modules API (`/api/v1`)

| Route | Rôle |
|-------|------|
| `/auth` | Inscription (+18), JWT, pause, auto-exclusion |
| `/fixtures` | Dashboard, recherche, détail match |
| `/predictions` | Historique, performance, interdiction suppression sélective |
| `/budget` | Limites, décisions, ROI |
| `/subscriptions` | Free/Premium/Pro, Stripe, Mobile Money hooks |
| `/notifications` | Préférences + consentement Telegram/WhatsApp |
| `/admin` | RBAC, sync, audit, annonces, sources |

## Sécurité

- JWT access/refresh, MFA admin, RBAC
- Rate limiting IP
- Quotas d'analyses par plan
- Secrets via environnement
- Service information-only (pas de wallet)
