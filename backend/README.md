# AidFinder Backend

API FastAPI de AidFinder. Elle gere l'authentification, les profils, les dashboards, l'administration, les recommandations, le scraping ANAPEC et le chatbot actuellement genere via Dify.

## Fonctionnalites

- Authentification JWT et OAuth2 Bearer.
- Roles utilisateur et administrateur.
- Profil utilisateur, theme, photo et mot de passe.
- Moderation admin avec avertissements, suspension et reactivation.
- Dashboard utilisateur, historique, aides recentes et recommandations.
- Chatbot avec streaming SSE.
- Generation principale des reponses via Dify (`response_generator.py` -> `dify_client.py`).
- `conversation_brain.py` utilise encore `llm_client.py` pour certaines analyses/extractions.
- Administration des utilisateurs, aides, sources, logs et statistiques.
- Scraping ANAPEC des offres d'emploi conserve.
- Scheduler de scraping toutes les 6 heures.

## Structure

```text
backend/
  app/
    core/
      config.py
      datetime_utils.py
      securite.py
      statuts_compte.py
    database/
      database.py
      session.py
    models/
      utilisateurs.py
      administrateur.py
      aides.py
      categorie_aide.py
      source_aide.py
      discussion.py
      historique.py
      resultat_chat.py
      consultation_aide.py
      document_requis.py
      export_pdf.py
      export_resultat.py
      notification.py
      action_moderation.py
      scraping_logs.py
    routes/
      auth.py
      users.py
      home.py
      dashboard.py
      admin.py
    schemas/
      utilisateur.py
      chat.py
      dashboard.py
      home.py
      admin.py
    services/
      auth_service.py
      user_service.py
      home_service.py
      dashboard_service.py
      admin_service.py
      chat_service.py
      conversation_brain.py
      conversation_engine.py
      response_generator.py
      dify_client.py
      llm_client.py
      recommendation_engine.py
    scraping/
      manager.py
      scheduler.py
      normalizer.py
      storage.py
      utils.py
      sources/anapec/emploi.py
      sources/anapec/news.py
    main.py
    create_tables.py
  tests/
  uploads/profiles/
  requirements.txt
```

## Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: `http://localhost:8000`  
Swagger: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

`app.main` cree les tables et applique les colonnes runtime necessaires au demarrage.

## Variables

Voir `.env.example`.

| Variable | Role |
| --- | --- |
| `DATABASE_URL` | Connexion PostgreSQL |
| `SECRET_KEY` | Signature JWT |
| `ALGORITHM` | Algorithme JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duree du token |
| `DIFY_API_KEY` | Cle API Dify |
| `DIFY_API_URL` | URL API Dify |
| `DIFY_USER` | Identifiant utilisateur Dify |
| `OPENROUTER_*` | Client LLM encore utilise pour analyses/fallbacks |
| `QWEN_*` | Fallback du client LLM |
| `SMTP_*` | Emails de moderation |
| `ANAPEC_EMPLOI_MAX_PAGES` | Nombre de pages recentes synchronisees en mode normal (`20` par defaut, `0`/`all` pour scan complet) |
| `CORS_ORIGINS` | Origines CORS |
| `CORS_ORIGIN_REGEX` | Regex CORS reseau local |

## Routes

| Prefixe | Role |
| --- | --- |
| `/auth` | inscription, connexion, desactivation |
| `/users` | profil, theme, mot de passe, photo |
| `/api/home` | accueil, stats, categories, recherche |
| `/dashboard` | dashboard utilisateur, chat, historique, recommandations |
| `/admin` | dashboard admin, utilisateurs, aides, sources, logs, statistiques |

Les routers dashboard et admin sont aussi montes sous `/api` pour compatibilite.

## Scraping

`app.scraping.scheduler.start_scheduler()` est lance au demarrage par FastAPI. Il execute `run_all_scrapers()` immediatement puis toutes les 6 heures.

- `sources/anapec/emploi.py`: scraper ANAPEC offres d'emploi, a conserver.
- `sources/anapec/news.py`: scraper actualites ANAPEC encore reference par le manager, non prioritaire.
- `storage.py`: normalisation, deduplication et insertion/mise a jour des aides.
- `scraping_logs.py`: journalisation en base.

## Chatbot

Le point principal de generation est `services/response_generator.py`, qui utilise Dify via `services/dify_client.py`. `ConversationMeta` conserve `dify_conversation_id`. Le systeme `llm_client.py` reste necessaire pour les fonctions d'analyse/extraction utilisees par `conversation_brain.py`.

## Validation

```bash
python -m pytest
python -m compileall app tests
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
