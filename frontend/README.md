# AidFinder Frontend

Interface React de AidFinder, construite avec Vite, Tailwind CSS v4, ShadCN/Radix, React Router, Axios, Framer Motion et Lucide.

## Fonctionnalites

- Pages publiques: accueil, inscription, connexion.
- Routage protege par role utilisateur/admin.
- Dashboard utilisateur.
- Profil, photo, theme et changement de mot de passe.
- Discussion chatbot avec streaming SSE.
- Historique de conversations et reprise d'une discussion.
- Aides recommandees et aides recentes.
- Administration: tableau de bord, utilisateurs, aides, statistiques.
- Toasts et navigation responsive.

La page frontend de gestion des sources scraping n'est pas exposee dans l'application actuelle. Les routes backend correspondantes restent disponibles.

## Structure

```text
frontend/
  components/ui/       Button, Card, Dialog, Input, Label, Skeleton
  lib/utils.js         helper cn()
  public/              favicon et assets publics
  src/
    assets/images/     logo et image d'accueil
    components/        composants metier
    config/env.js      detection URL API
    constants/         options de profil
    contexts/          Auth, Profile, Theme, Toast
    hooks/             dashboard, admin, recommandations, streaming chat
    layouts/           public, dashboard utilisateur, dashboard admin
    pages/             pages routees
    services/          clients API Axios
    utils/             dates, erreurs, aides, navigation, profil
```

## Installation

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Application: `http://localhost:5173`.

## Variables

| Variable | Description | Defaut |
| --- | --- | --- |
| `VITE_API_PORT` | Port backend si `VITE_API_URL` est absent | `8000` |
| `VITE_API_URL` | URL complete de l'API | deduite du navigateur |

Sans `VITE_API_URL`, le frontend appelle le backend sur le meme hote que la page, avec le port `VITE_API_PORT`.

## Routes principales

| Route | Page |
| --- | --- |
| `/` | Accueil |
| `/login` | Connexion |
| `/register` | Inscription |
| `/dashboard` | Dashboard utilisateur |
| `/dashboard/profil` | Profil |
| `/dashboard/changer-mot-de-passe` | Mot de passe |
| `/dashboard/discussion` | Discussion |
| `/dashboard/discussion/:id` | Reprise discussion |
| `/dashboard/historique` | Historique |
| `/dashboard/aides-recommandees` | Recommandations |
| `/admin` | Dashboard admin |
| `/admin/utilisateurs` | Gestion utilisateurs |
| `/admin/aides` | Gestion aides |
| `/admin/statistiques` | Statistiques |
| `/admin/profil` | Profil admin |

## Scripts

```bash
npm run dev
npm run build
npm run lint
npm run preview
```
