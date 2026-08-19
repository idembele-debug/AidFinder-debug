"""
Scraper des offres d'emploi ANAPEC.

Point d'entrée exclusif : https://anapec.ma/chercheurs/offres

Fonctionnement :
  - Le site utilise Laravel Livewire 3 pour rendre les offres.
  - La page HTML contient un attribut wire:snapshot avec un JSON
    qui embarque la première page d'offres (15 offres) ainsi que
    les informations de pagination (total pages, page suivante).
  - Les pages suivantes sont récupérées via des requêtes POST
    vers l'endpoint Livewire 3 /livewire-.../update.
  - Le point d'entrée unique et exclusif est https://anapec.ma.

Compatible avec manager.py, scheduler.py, storage.py, normalizer.py et utils.py.
"""

from app.scraping.utils import log_scraping_error
from app.scraping.normalizer import normalize_record
import requests
import re
import json
import html as html_module
import time
import os
from time import perf_counter


# ── Constantes ─────────────────────────────────────────────────
BASE_URL = "https://anapec.ma"
START_URL = "https://anapec.ma/chercheurs/offres"
SOURCE_NAME = "ANAPEC"
SOURCE_TYPE = "Organisme public"
CATEGORY_NAME = "Offres d'emploi"
MAX_PAGES = 1000  # sécurité
OFFERS_PER_PAGE = 15
LAST_METRICS = {}


def _default_max_pages() -> int:
    value = os.getenv("ANAPEC_EMPLOI_MAX_PAGES", "20").strip().lower()
    if value in {"", "all", "full", "0"}:
        return MAX_PAGES
    try:
        return max(1, min(int(value), MAX_PAGES))
    except ValueError:
        return 20


def _compute_full_scan(
    page_limit: int,
    total_pages_available: int,
    pages_fetched: int,
    pages_failed: int,
) -> bool:
    """Détermine si le scan a couvert toutes les pages nécessaires.

    full_scan n'est True QUE si :
      - toutes les pages disponibles ont été demandées (page_limit >= total) ;
      - aucune page n'a échoué (réseau, parsing, snapshot manquant) ;
      - le nombre de pages réellement récupérées couvre bien page_limit.

    Une page simplement tentée mais échouée ne compte PAS comme récupérée.
    """
    return (
        page_limit >= total_pages_available
        and pages_failed == 0
        and pages_fetched >= page_limit
    )


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
}

_SESSION = None


def _get_session() -> requests.Session:
    """Retourne une session requests persistante (réutilisée).

    Les headers User-Agent et les cookies sont conservés
    automatiquement entre les requêtes.
    """
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update(_HEADERS)
    return _SESSION


# Erreurs réseau considérées comme temporaires → retry possible
_RETRYABLE_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ReadTimeout,
    requests.exceptions.ConnectTimeout,
    ConnectionResetError,
    ConnectionRefusedError,
    ConnectionAbortedError,
    ConnectionError,
)

# Délais entre chaque tentative (exponentiel : 2s, 4s, 8s, 16s)
_RETRY_DELAYS = [2, 4, 8, 16]

# Mots-clés dans le message d'erreur indiquant une panne réseau
_RETRYABLE_KEYWORDS = [
    "network is down",
    "temporary failure",
    "connection reset",
    "connection refused",
    "name or service not known",
    "no route to host",
]


def _extract_wire_snapshot(html_text: str) -> dict | None:
    """Extrait le wire:snapshot du composant pages::chercheurs.offres."""
    pattern = r'wire:snapshot="([^"]+)"'
    matches = re.findall(pattern, html_text)
    for raw_snap in matches:
        decoded = html_module.unescape(raw_snap)
        try:
            data = json.loads(decoded)
            if data.get("memo", {}).get("name") == "pages::chercheurs.offres":
                return data
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _extract_raw_snapshot(html_text: str) -> str | None:
    """Extrait la chaîne brute du snapshot Livewire (non parsée)."""
    pattern = r'wire:snapshot="([^"]+)"'
    matches = re.findall(pattern, html_text)
    for raw_snap in matches:
        decoded = html_module.unescape(raw_snap)
        try:
            data = json.loads(decoded)
            if data.get("memo", {}).get("name") == "pages::chercheurs.offres":
                return decoded
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _extract_raw_snapshot_from_response(livewire_response: dict) -> str | None:
    """Extrait la chaîne brute du snapshot depuis une réponse Livewire 3."""
    components = livewire_response.get("components", [])
    if not components:
        return None
    raw = components[0].get("snapshot", "")
    if not raw:
        return None
    # Si c'est déjà un dict, on re-sérialise
    if isinstance(raw, dict):
        return json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
    return raw


def _extract_offers_from_snapshot(snapshot: dict) -> list[dict]:
    """Extrait la liste des offres depuis le snapshot Livewire.

    Les offres se trouvent dans data.latestOffers sous la forme :
        latestOffers = [
            [ [offre, {"s":"arr"}], [offre, {"s":"arr"}] ],
            {"s":"arr"}
        ]
    """
    latest_offers = snapshot.get("data", {}).get("latestOffers", [])
    if not isinstance(latest_offers, list) or len(latest_offers) == 0:
        return []
    page_wrappers = latest_offers[0]
    if not isinstance(page_wrappers, list):
        return []
    offers = []
    for item in page_wrappers:
        if isinstance(item, list) and len(item) > 0 and isinstance(item[0], dict):
            offers.append(item[0])
    return offers


def _extract_pagination_info(snapshot: dict) -> dict:
    """Extrait les informations de pagination depuis le snapshot."""
    info = {"total_offers": 0, "total_pages": 1}
    paginate = snapshot.get("data", {}).get("paginate", [])
    if isinstance(paginate, list) and len(paginate) > 0:
        pag_data = paginate[0]
        if isinstance(pag_data, dict):
            count = pag_data.get("count", "0")
            info["total_offers"] = int(count) if count else 0
            last_url = pag_data.get("last", "")
            if last_url:
                match = re.search(r"page:(\d+)", str(last_url))
                if match:
                    info["total_pages"] = int(match.group(1))
    return info


def _extract_component_id(snapshot: dict) -> str | None:
    """Extrait l'identifiant du composant Livewire."""
    return snapshot.get("memo", {}).get("id")


def _extract_livewire_config(html_text: str) -> tuple[str | None, str | None]:
    """Extrait le token CSRF et l'URI update depuis la page HTML."""
    match = re.search(
        r'<script[^>]+data-csrf="([^"]+)"[^>]+data-update-uri="([^"]+)"',
        html_text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1), match.group(2)
    return None, None


def _fetch_page(
    page: int,
    csrf_token: str,
    cookies: dict,
    component_id: str,
    snapshot_str: str,
    update_uri: str,
    session: requests.Session | None = None,
) -> dict | None:
    """Récupère une page d'offres via l'API Livewire 3.

    Effectue jusqu'à 5 tentatives avec backoff exponentiel (2s, 4s, 8s, 16s)
    pour les erreurs réseau temporaires (ConnectionError, Timeout, etc.).

    Utilise la session requests persistante (si fournie) pour conserver
    les headers Livewire et les cookies entre les pages.
    """
    headers = {
        "User-Agent": _HEADERS["User-Agent"],
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Livewire": "true",
        "X-CSRF-TOKEN": csrf_token,
        "Referer": START_URL,
        "X-Requested-With": "XMLHttpRequest",
    }

    payload = {
        "_token": csrf_token,
        "components": [
            {
                "snapshot": snapshot_str,
                "updates": {},
                "calls": [
                    {
                        "path": "",
                        "method": "goToPage",
                        "params": [page],
                    }
                ],
            }
        ],
    }

    http = session if session else requests

    for attempt in range(1, 6):  # 5 tentatives max
        if attempt > 1:
            delay = _RETRY_DELAYS[attempt - 2]
            print(f"  Erreur réseau. Nouvelle tentative dans {delay} secondes.")
            time.sleep(delay)

        print(f"  Tentative {attempt}/5")
        try:
            response = http.post(
                update_uri,
                json=payload,
                headers=headers,
                cookies=cookies,
                timeout=15,
            )
            if response.status_code == 419:
                log_scraping_error(
                    f"anapec_emploi_livewire_page_{page}",
                    "419 CSRF mismatch",
                )
                return None
            response.raise_for_status()
            # Succès après une ou plusieurs tentatives
            if attempt > 1:
                print(f"  Connexion rétablie.")
            return response.json()

        except _RETRYABLE_ERRORS:
            log_scraping_error(
                f"anapec_emploi_livewire_page_{page}_attempt_{attempt}",
                "Erreur réseau (retryable)",
            )
            if attempt == 5:
                print(f"  Abandon de la page {page} après 5 tentatives.")
                return None
            continue  # Nouvelle tentative

        except requests.exceptions.RequestException as e:
            error_msg = str(e).lower()
            is_retryable = any(kw in error_msg for kw in _RETRYABLE_KEYWORDS)
            if is_retryable and attempt < 5:
                # Erreur avec mot-clé réseau, on retente
                continue
            # Erreur HTTP non retryable (4xx, 5xx classique…) → abandon
            log_scraping_error(
                f"anapec_emploi_livewire_page_{page}",
                str(e),
            )
            return None

        except Exception as e:
            log_scraping_error(
                f"anapec_emploi_livewire_page_{page}",
                str(e),
            )
            return None

    return None


def fetch_listings(metrics: dict | None = None, max_pages: int | None = None) -> list[dict]:
    """Récupère toutes les offres d'emploi via Livewire.

    1. Télécharge la page initiale (page 1, déjà dans le snapshot).
    2. Extrait les infos de pagination.
    3. Parcourt les pages suivantes via des requêtes POST Livewire.
    """
    all_offers: list[dict] = []

    # ── 1. Page initiale ──────────────────────────────────────
    print(f"[ANAPEC-EMPLOI] Téléchargement de {START_URL}")
    session = _get_session()
    try:
        started = perf_counter()
        response = session.get(START_URL, timeout=15)
        response.raise_for_status()
        if metrics is not None:
            metrics["http_seconds"] += perf_counter() - started
        html_text = response.text
        cookies = response.cookies
    except Exception as e:
        if metrics is not None:
            metrics["errors"] += 1
        log_scraping_error("anapec_emploi_init", str(e))
        print(f"[ANAPEC-EMPLOI] Erreur accès à {START_URL}: {e}")
        return all_offers

    # Extraire le snapshot et sa chaîne brute
    started = perf_counter()
    snapshot = _extract_wire_snapshot(html_text)
    if not snapshot:
        if metrics is not None:
            metrics["errors"] += 1
        print("[ANAPEC-EMPLOI] Aucun snapshot Livewire trouvé.")
        return all_offers

    snapshot_str = _extract_raw_snapshot(html_text)
    if not snapshot_str:
        if metrics is not None:
            metrics["errors"] += 1
        print("[ANAPEC-EMPLOI] Impossible d'extraire le snapshot brut.")
        return all_offers
    if metrics is not None:
        metrics["parsing_seconds"] += perf_counter() - started

    # Extraire les offres de la page 1
    started = perf_counter()
    page_offers = _extract_offers_from_snapshot(snapshot)
    all_offers.extend(page_offers)
    print(f"[ANAPEC-EMPLOI] Page 1 : {len(page_offers)} offres")
    if metrics is not None:
        metrics["parsing_seconds"] += perf_counter() - started
        metrics["pages"] = 1

    # Infos de pagination
    info = _extract_pagination_info(snapshot)
    total_pages_available = min(info["total_pages"], MAX_PAGES)
    page_limit = min(total_pages_available, max_pages or _default_max_pages())
    print(f"[ANAPEC-EMPLOI] Pages totales : {total_pages_available}")
    if page_limit < total_pages_available:
        print(f"[ANAPEC-EMPLOI] Synchronisation incrémentale limitée à {page_limit} pages")
    if metrics is not None:
        metrics["total_pages_available"] = total_pages_available
        metrics["page_limit"] = page_limit
        # full_scan est recalculé après la boucle, une fois que l'on sait
        # si toutes les pages ont réellement été récupérées avec succès.
        metrics["full_scan"] = False

    # Extraire le CSRF token et l'URI update
    csrf_token, update_uri = _extract_livewire_config(html_text)
    if not csrf_token or not update_uri:
        if metrics is not None:
            metrics["errors"] += 1
        print("[ANAPEC-EMPLOI] Aucune config Livewire trouvée.")
        return all_offers
    print(f"[ANAPEC-EMPLOI] Livewire update URI: {update_uri}")

    # Extraire l'ID du composant
    component_id = _extract_component_id(snapshot)
    if not component_id:
        if metrics is not None:
            metrics["errors"] += 1
        print("[ANAPEC-EMPLOI] Aucun ID de composant trouvé.")
        return all_offers

    # ── 2. Pages suivantes ────────────────────────────────────
    current_snapshot_str = snapshot_str
    page = 1
    # La page 1 a déjà été récupérée avec succès au-dessus.
    pages_fetched = 1
    pages_failed = 0
    while page < page_limit:
        page += 1

        print(f"[ANAPEC-EMPLOI] Page {page}/{page_limit}...")
        started = perf_counter()
        livewire_data = _fetch_page(
            page, csrf_token, cookies, component_id, current_snapshot_str, update_uri, session
        )
        if metrics is not None:
            metrics["http_seconds"] += perf_counter() - started
            metrics["pages"] = page

        if not livewire_data:
            if metrics is not None:
                metrics["errors"] += 1
            pages_failed += 1
            print(f"[ANAPEC-EMPLOI] Page {page} impossible après 5 tentatives.")
            continue

        # Extraire le nouveau snapshot brut de la réponse
        started = perf_counter()
        new_raw = _extract_raw_snapshot_from_response(livewire_data)
        if not new_raw:
            if metrics is not None:
                metrics["errors"] += 1
            pages_failed += 1
            print(f"[ANAPEC-EMPLOI] Aucun snapshot dans la réponse page {page}.")
            break

        # Parser pour extraire les offres
        try:
            new_data = json.loads(new_raw)
        except json.JSONDecodeError:
            if metrics is not None:
                metrics["errors"] += 1
            pages_failed += 1
            print(f"[ANAPEC-EMPLOI] Erreur parsing snapshot page {page}.")
            break

        page_offers = _extract_offers_from_snapshot(new_data)
        if not page_offers:
            print(f"[ANAPEC-EMPLOI] Page {page} vide, arrêt.")
            break

        all_offers.extend(page_offers)
        pages_fetched += 1
        if metrics is not None:
            metrics["parsing_seconds"] += perf_counter() - started
        print(f"[ANAPEC-EMPLOI] Page {page} : {len(page_offers)} offres "
              f"(total : {len(all_offers)})")

        # Mettre à jour l'ID du composant (peut changer)
        new_id = _extract_component_id(new_data)
        if new_id:
            component_id = new_id

        # Utiliser le nouveau snapshot pour la page suivante
        current_snapshot_str = new_raw

    # ── 3. Calcul de full_scan (sécurité soft-disable) ────────
    # full_scan n'est True QUE si toutes les pages nécessaires ont
    # effectivement été récupérées avec succès. Une page simplement
    # tentée mais échouée ne compte pas comme récupérée.
    if metrics is not None:
        metrics["pages_fetched"] = pages_fetched
        metrics["pages_failed"] = pages_failed
        metrics["full_scan"] = _compute_full_scan(
            page_limit,
            total_pages_available,
            pages_fetched,
            pages_failed,
        )

    print(f"[ANAPEC-EMPLOI] Total offres récupérées : {len(all_offers)}")
    return all_offers


def parse_listing(offer_data: dict) -> dict | None:
    """Convertit une offre brute du snapshot en enregistrement normalisé."""
    if not offer_data or not isinstance(offer_data, dict):
        return None

    offer_id = offer_data.get("id")
    titre = offer_data.get("intitule_poste")
    lieu = (offer_data.get("lieu_travail") or "").strip()
    reference = offer_data.get("ref_offre")
    entreprise = offer_data.get("entreprise")
    date_offre = offer_data.get("date_offre")
    stable_id = str(offer_id or reference or "").strip()

    if not stable_id or not titre:
        return None

    url_officielle = f"{BASE_URL}/chercheurs/offres"

    description = f"{titre}"
    if lieu:
        description += f" - {lieu}"
    if entreprise and entreprise not in ("-", "", None):
        if not entreprise.startswith("http"):
            description += f" - {entreprise}"

    data = {
        "source_nom": SOURCE_NAME,
        "source_url": BASE_URL,
        "source_type": SOURCE_TYPE,
        "source_fiable": True,
        "categorie_nom": CATEGORY_NAME,
        "categorie_description": (
            "Offres d'emploi publiées par les employeurs via l'ANAPEC."
        ),
        "titre": titre,
        "description": description,
        "date_limite": None,
        "type_aide": "Offre d'emploi",
        "montant": None,
        "age_min": None,
        "age_max": None,
        "region_cible": lieu or "Maroc",
        "niveau_etude_requis": None,
        "statut_socio_pro_requis": None,
        "handicap_requis": False,
        "url_officielle": url_officielle,
        "image_url": None,
        "source_record_id": f"anapec_emploi:{stable_id}",
        "reference_offre": reference,
        "entreprise_nom": entreprise if entreprise and entreprise != "-" else None,
        "date_publication": date_offre,
        "lieu_travail": lieu,
    }

    return normalize_record(data)


def scrape_emploi(max_pages: int | None = None):
    """Lance le scraping complet des offres d'emploi ANAPEC.

    Point d'entrée exclusif : https://anapec.ma/chercheurs/offres.
    """
    print("[ANAPEC-EMPLOI] Début du scraping des offres d'emploi")
    started_total = perf_counter()
    metrics = {
        "pages": 0,
        "total_pages_available": 0,
        "page_limit": 0,
        "full_scan": False,
        "offers": 0,
        "records": 0,
        "errors": 0,
        "http_seconds": 0.0,
        "parsing_seconds": 0.0,
        "processing_seconds": 0.0,
        "total_seconds": 0.0,
    }
    records = []

    try:
        offers = fetch_listings(metrics, max_pages=max_pages)
        metrics["offers"] = len(offers)
        print(f"[ANAPEC-EMPLOI] {len(offers)} offres à traiter")

        started_processing = perf_counter()
        for i, offer in enumerate(offers, 1):
            try:
                record = parse_listing(offer)
                if record:
                    records.append(record)
                else:
                    metrics["errors"] += 1
            except Exception as exc:
                metrics["errors"] += 1
                log_scraping_error(f"anapec_emploi_offer_{i}", str(exc))
        metrics["processing_seconds"] = perf_counter() - started_processing

    except Exception as e:
        metrics["errors"] += 1
        log_scraping_error("anapec_emploi", str(e))
        print(f"[ANAPEC-EMPLOI] Erreur : {e}")

    metrics["records"] = len(records)
    metrics["total_seconds"] = perf_counter() - started_total
    global LAST_METRICS
    LAST_METRICS = metrics
    print(f"[ANAPEC-EMPLOI] {len(records)} enregistrements récupérés")
    print(
        "[ANAPEC-EMPLOI] Metrics: "
        f"pages={metrics['pages']} offres={metrics['offers']} "
        f"http={metrics['http_seconds']:.2f}s parsing={metrics['parsing_seconds']:.2f}s "
        f"processing={metrics['processing_seconds']:.2f}s total={metrics['total_seconds']:.2f}s "
        f"errors={metrics['errors']}"
    )
    return records


def get_last_metrics() -> dict:
    return dict(LAST_METRICS)
