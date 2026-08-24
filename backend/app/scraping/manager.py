from datetime import datetime
from threading import Lock
from time import perf_counter

from app.core.datetime_utils import utc_now
from app.database.database import SessionLocal
from app.models.scraping_logs import ScrapingLog
from app.scraping.sources.anapec import scrape_emploi
from app.scraping.sources.anapec.emploi import get_last_metrics
from app.scraping.storage import save_records


SCRAPERS = {
    "anapec_emploi": {
        "label": "ANAPEC",
        "scraper": scrape_emploi,
        "deactivate_missing": True,
        "metrics": get_last_metrics,
    },
}

DEFAULT_SCRAPERS = ("anapec_emploi",)
SCRAPER_LOCKS = {name: Lock() for name in SCRAPERS}


def _empty_stats() -> dict:
    return {
        "records": 0,
        "new_records": 0,
        "updated_records": 0,
        "unchanged_records": 0,
        "duplicate_records": 0,
        "expired_records": 0,
        "errors": 0,
        "database_seconds": 0.0,
        "total_seconds": 0.0,
    }


def _create_scraping_log(source: str, started_at: datetime) -> int:
    db = SessionLocal()
    try:
        log = ScrapingLog(
            source=source,
            started_at=started_at,
            finished_at=None,
            duration=None,
            new_records=0,
            updated_records=0,
            expired_records=0,
            status="running",
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log.scraplogs_id
    finally:
        db.close()


def _finish_scraping_log(
    log_id: int,
    started_at: datetime,
    finished_at: datetime,
    stats: dict,
    status: str,
    error_message: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        log = db.query(ScrapingLog).filter(ScrapingLog.scraplogs_id == log_id).first()
        if log is None:
            return
        log.finished_at = finished_at
        log.duration = str(finished_at - started_at)
        log.new_records = stats.get("new_records", 0)
        log.updated_records = stats.get("updated_records", 0)
        log.expired_records = stats.get("expired_records", 0)
        log.status = status
        log.error_message = error_message
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_scraper(scraper_name: str) -> dict:
    config = SCRAPERS[scraper_name]
    stats = _empty_stats()
    lock = SCRAPER_LOCKS[scraper_name]
    if not lock.acquire(blocking=False):
        stats["scraper"] = scraper_name
        stats["source"] = config["label"]
        stats["status"] = "already_running"
        print(f"[ANAPEC SCRAPER] {scraper_name} déjà en cours, relance ignorée.")
        return stats

    started_at = utc_now()
    started_perf = perf_counter()
    log_id = _create_scraping_log(config["label"], started_at)

    try:
        records = config["scraper"]()
        scrape_metrics = config["metrics"]()
        deactivate_missing = config["deactivate_missing"] and scrape_metrics.get("full_scan", False)
        db_started = perf_counter()
        sync_stats = save_records(
            records,
            deactivate_missing=deactivate_missing,
        )
        stats.update(sync_stats)
        stats["errors"] = sync_stats.get("errors", 0) + scrape_metrics.get("errors", 0)
        stats["database_seconds"] = perf_counter() - db_started
        stats["total_seconds"] = perf_counter() - started_perf
        stats["scraper"] = scraper_name
        stats["source"] = config["label"]
        stats["metrics"] = scrape_metrics
        stats["deactivate_missing"] = deactivate_missing

        status = "success" if stats["errors"] == 0 else "partial_success"
        stats["status"] = status
        _finish_scraping_log(log_id, started_at, utc_now(), stats, status)
        _print_summary(stats)
        return stats
    except Exception as exc:
        stats["errors"] += 1
        stats["total_seconds"] = perf_counter() - started_perf
        stats["status"] = "failed"
        _finish_scraping_log(log_id, started_at, utc_now(), stats, "failed", str(exc))
        raise
    finally:
        lock.release()


def run_all_scrapers(scraper_names: tuple[str, ...] | list[str] | None = None) -> dict:
    "Lance les scrapers demandés et retourne des statistiques agrégées."
    selected = tuple(scraper_names or DEFAULT_SCRAPERS)
    aggregate = _empty_stats()
    aggregate["scrapers"] = []

    for scraper_name in selected:
        if scraper_name not in SCRAPERS:
            raise ValueError(f"Scraper inconnu: {scraper_name}")
        try:
            result = run_scraper(scraper_name)
            aggregate["scrapers"].append(result)
            for key in (
                "records",
                "new_records",
                "updated_records",
                "unchanged_records",
                "duplicate_records",
                "expired_records",
                "errors",
            ):
                aggregate[key] += result.get(key, 0)
            aggregate["database_seconds"] += result.get("database_seconds", 0.0)
            aggregate["total_seconds"] += result.get("total_seconds", 0.0)
        except Exception as exc:
            aggregate["errors"] += 1
            aggregate["scrapers"].append(
                {
                    "scraper": scraper_name,
                    "source": SCRAPERS[scraper_name]["label"],
                    "status": "failed",
                    "error": str(exc),
                }
            )
            print(f"Error occurred with {scraper_name}: {exc}")

    return aggregate


def _print_summary(stats: dict) -> None:
    metrics = stats.get("metrics") or {}
    print("[ANAPEC SCRAPER]")
    print(f"Pages analysées       : {metrics.get('pages', 0)}")
    print(f"Offres trouvées       : {metrics.get('offers', stats.get('records', 0))}")
    print(f"Nouvelles             : {stats.get('new_records', 0)}")
    print(f"Mises à jour          : {stats.get('updated_records', 0)}")
    print(f"Inchangées            : {stats.get('unchanged_records', 0)}")
    print(f"Doublons ignorés      : {stats.get('duplicate_records', 0)}")
    print(f"Désactivées           : {stats.get('expired_records', 0)}")
    print(f"Erreurs               : {stats.get('errors', 0)}")
    print(f"HTTP                  : {metrics.get('http_seconds', 0.0):.2f}s")
    print(f"Parsing               : {metrics.get('parsing_seconds', 0.0):.2f}s")
    print(f"Traitement            : {metrics.get('processing_seconds', 0.0):.2f}s")
    print(f"Database              : {stats.get('database_seconds', 0.0):.2f}s")
    print(f"Total                 : {stats.get('total_seconds', 0.0):.2f}s")
