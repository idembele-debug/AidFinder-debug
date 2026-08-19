import re, hashlib
from datetime import datetime

def normalize_text(text):
    "nettoie un texte en supprimant les espaces inutilles"
    if text is None:
        return None
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)  # remplace les espaces multiples par un seul espace
    return text if text else None

def normalize_title(title):
    "nettoie un titre"
    title = normalize_text(title)
    if title:
        return title.capitalize()
    return None

def normalize_description(description):
    "normalise une description"
    return normalize_text(description)

def normalize_date(date_value):
    "conveertit date vers un objet date"
    if not date_value:
        return None
    date_value = normalize_text(date_value)
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_value, fmt).date()
        except ValueError:
            continue
    return None  # si aucun format ne correspond

def normalize_amount(amount):
    "Extrait un montant numerique"
    if amount is None:
        return None
    amount = normalize_text(amount)
    numbers = re.findall(r"\d+[.,]?\d*", amount)
    if not numbers:
        return None
    # On prend le premier nombre trouvé et on le convertit en float
    value = numbers[0].replace(',', '.')
    return float(value)

def normalize_age(age):
    "convertit un age"
    if age is None:
        return None
    numbers = re.findall(r"\d+", str(age))
    if not numbers:
        return None
    return int(numbers[0])

def normalize_region(region):
    "normalise une région"
    return normalize_text(region)

def normalize_level(level):
    "normalise un niveau d'etude"
    level = normalize_text(level)
    if level is None:
        return None
    level = level.lower()
    mapping = {
        "bac":"Bac",
        "licence": "Licence",
        "master": "Master",
        "doctorat": "Doctorat",
        "tous": "Tous"
    }
    for key, value in mapping.items():
        if key in level:
            return value
    return level.capitalize()

def normalize_status(status):
    "normalise un statut"
    return normalize_text(status)

def normalize_boolean(value):
    "convertit differentes representations booléennes"
    if isinstance(value, bool):
        return value
    
    if value is None:
        return False
    value = str(value).strip().lower()
    return value in ['true', '1', 'yes', 'oui', 'vrai']

def generate_content_hash(record):
    "génère un hash perettant de detecter les modifications"
    content = (
    f"{record.get('titre','')}"
    f"{record.get('description','')}"
    f"{record.get('type_aide','')}"
    f"{record.get('date_limite','')}"
    f"{record.get('montant','')}"
    f"{record.get('region_cible','')}"
    f"{record.get('niveau_etude_requis','')}"
    f"{record.get('statut_socio_pro_requis','')}"
    f"{record.get('url_officielle','')}"
    f"{record.get('reference_offre','')}"
    f"{record.get('entreprise_nom','')}"
    f"{record.get('date_publication','')}"
    f"{record.get('lieu_travail','')}"
)
    return hashlib.sha256(content.encode()).hexdigest()

def normalize_record(data):
    "normalise complètement une aide"

    normalized = {
        "source_nom": normalize_text(data.get("source_nom")),
        "source_url": normalize_text(data.get("source_url")),
        "source_type": normalize_text(data.get("source_type")),
        "source_fiable": normalize_boolean(data.get("source_fiable", True)),
        "categorie_nom": normalize_text(data.get("categorie_nom")),
        "categorie_description": normalize_text(data.get("categorie_description")),
        "titre": normalize_title(data.get("titre")),
        "description": normalize_description(data.get("description")),
        "date_limite": normalize_date(data.get("date_limite")),
        "type_aide": normalize_text(data.get("type_aide")),
        "montant": normalize_amount(data.get("montant")),
        "age_min": normalize_age(data.get("age_min")),
        "age_max": normalize_age(data.get("age_max")),
        "region_cible": normalize_region(data.get("region_cible")),
        "niveau_etude_requis": normalize_level(data.get("niveau_etude_requis")),
        "statut_socio_pro_requis": normalize_status(data.get("statut_socio_pro_requis")),
        "handicap_requis": normalize_boolean(data.get("handicap_requis")),
        "url_officielle": normalize_text(data.get("url_officielle")),
        "image_url": normalize_text(data.get("image_url")),
        "source_record_id": normalize_text(data.get("source_record_id")),
        "reference_offre": normalize_text(data.get("reference_offre")),
        "entreprise_nom": normalize_text(data.get("entreprise_nom")),
        "date_publication": normalize_date(data.get("date_publication")),
        "lieu_travail": normalize_text(data.get("lieu_travail")),
    }

    normalized["content_hash"] = generate_content_hash(normalized)

    return normalized
