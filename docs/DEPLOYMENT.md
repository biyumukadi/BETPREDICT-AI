# Déploiement production — BETPREDICT AI

## Architecture cible

```
Internet → CDN / Reverse proxy (TLS)
        → Next.js (frontend PWA)
        → FastAPI (API)
        → PostgreSQL + Redis
        → Celery worker (+ beat)
        → MLflow (optionnel)
```

## Checklist sécurité

1. Générer un `SECRET_KEY` fort (≥ 48 caractères)
2. Désactiver `APP_DEBUG`
3. Restreindre `CORS_ORIGINS` aux domaines officiels
4. Secrets via vault / secret manager (jamais dans le dépôt)
5. MFA obligatoire pour les administrateurs
6. Rate limiting au reverse proxy + middleware API
7. Sauvegardes PostgreSQL quotidiennes chiffrées
8. Journalisation centralisée (audit_logs + access logs)
9. Vérifier les licences des fournisseurs de données et de cotes
10. Mentions légales paris / publicité selon la juridiction

## Variables critiques

Voir `.env.example`. En production :

- `DEMO_MODE=false` uniquement si un fournisseur licencié est configuré
- `STRIPE_SECRET_KEY` + webhook secret
- Credentials Mobile Money régionaux si applicable
- `DATABASE_URL` / Redis sur réseau privé

## Build images

```bash
docker compose build
```

Pour un déploiement Kubernetes / Cloud Run, publier les images `backend` et `frontend` vers votre registry, puis :

1. Appliquer migrations : `alembic upgrade head`
2. Lancer seed uniquement en environnement de staging
3. Démarrer `uvicorn` sans `--reload`
4. Démarrer Celery worker + beat
5. Servir Next.js via `next start` derrière un reverse proxy

## Reverse proxy (exemple Nginx)

- Terminer TLS
- Proxy `/` → frontend:3000
- Proxy `/api` et `/docs` → backend:8000
- Headers `X-Forwarded-*` et HSTS

## Observabilité

- Healthcheck : `GET /health`
- Métriques modèles : MLflow (`MLFLOW_TRACKING_URI`)
- Alertes sur erreurs d'import (`DataSourceConfig.last_error`)
- Audit admin via `/api/v1/admin/audit-logs`

## Abonnements

- Stripe Checkout + webhooks
- Mobile Money : activer les adaptateurs après obtention des credentials licenciés
- Les plans Free / Premium / Pro limitent les analyses quotidiennes côté API

## Mise à jour

1. Déployer backend compatible (migrations forward-only)
2. Déployer frontend
3. Redémarrer workers Celery
4. Vérifier `/health` et un dashboard démo/staging

## Avertissement réglementaire

BETPREDICT AI est un service d'analyse statistique. Il ne constitue pas un bookmaker, n'accepte aucune mise et ne conserve aucun fonds. Obtenez les autorisations locales nécessaires avant toute commercialisation liée aux paris sportifs.
