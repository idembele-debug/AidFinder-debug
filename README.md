# AidFinder

AidFinder est une plateforme web pour centraliser et presenter des aides, opportunites et offres utiles aux utilisateurs au Maroc.

Le projet contient un frontend React, une API FastAPI, une base PostgreSQL, un systeme d'authentification, des profils utilisateurs, des recommandations d'aides, du scraping ANAPEC et un chatbot actuellement branche sur Dify.

## Architecture

```text
frontend/ React 19 + Vite + Tailwind
    -> API HTTP
backend/ FastAPI + SQLAlchemy
    -> services metier
    -> PostgreSQL / Dify / scrapers ANAPEC
```

## Fonctionnalites actuelles

- Authentification JWT, inscription, connexion et desactivation volontaire.
- Roles `utilisateur` et `administrateur`.
- Profil utilisateur, photo, theme et changement de mot de passe.
- Dashboard utilisateur avec historique, aides recentes et recommandations.
- Interface de discussion avec streaming SSE.
- Generation principale du chatbot via Dify.
- Extraction/analyse conversationnelle encore appuyee par `llm_client` quand necessaire.
- Administration des utilisateurs, aides et statistiques.
- Routes backend de sources/logs scraping conservees.
- Scraping ANAPEC **offres d'emploi** conserve et planifie (source de scraping active et unique).

Le scraping des actualites ANAPEC a ete supprime : seul le scraping des offres d'emploi ANAPEC est conserve. Le chatbot existe et genere ses reponses via Dify, mais il n'est pas considere comme termine.

## Structure

```text
backend/
  app/
    core/        configuration, securite, dates, statuts
    database/    connexion SQLAlchemy et sessions
    models/      modeles SQLAlchemy
    routes/      routes auth, users, home, dashboard, admin
    schemas/     schemas Pydantic
    services/    auth, profil, admin, dashboard, chat, Dify, LLM, recommandations
    scraping/    scheduler, manager, stockage, normalisation, sources ANAPEC
  tests/
  uploads/
  requirements.txt

frontend/
  components/ui/ composants UI reutilisables
  lib/
  public/
  src/
    components/
    contexts/
    hooks/
    layouts/
    pages/
    services/
    utils/
  package.json

docs/
  maquettes, UML, architecture, planning, livrables
```

## Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Le backend cree et ajuste le schema au demarrage via `app.main`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## URLs

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:5173` |
| Backend | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |

## Variables

Backend: voir `backend/.env.example`.

Variables principales:

- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DIFY_API_KEY`
- `DIFY_API_URL`
- `DIFY_USER`
- `OPENROUTER_*` et `QWEN_*` pour le client LLM encore utilise hors generation principale
- `CORS_ORIGINS`
- `CORS_ORIGIN_REGEX`

Frontend: voir `frontend/.env.example`.

- `VITE_API_PORT`
- `VITE_API_URL` optionnel

## Scraping

Le scheduler backend lance `app.scraping.manager.run_all_scrapers()` au demarrage puis toutes les 6 heures. La seule source de scraping active est **ANAPEC offres d'emploi** (`app/scraping/sources/anapec/emploi.py`). Le scraper d'actualites ANAPEC (`news.py`) a ete supprime.

## Validation

Commandes utiles:

```bash
cd backend && python -m pytest
cd frontend && npm run lint
cd frontend && npm run build
```
