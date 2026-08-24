import logging

# logger du module
logger = logging.getLogger(__name__)


def log_scraping_error(source, error):
    """journalise une erreur de scraping"""
    logger.error("[%s] Erreur de scraping: %s", source, str(error))