from typing import Dict, List
from models.event import EventPreview
from services.event_validator import validate_event


def event_publication_status(event: EventPreview) -> Dict:
    """
    Determina se un evento è pronto alla pubblicazione.
    """

    missing_fields: List[str] = []

    # --- CAMPI OBBLIGATORI ---
    if not event.name:
        missing_fields.append("name")

    if not event.date:
        missing_fields.append("date")

    if not event.venue:
        missing_fields.append("venue")
    else:
        if not event.venue.address:
            missing_fields.append("venue.address")
        if not event.venue.city:
            missing_fields.append("venue.city")

    if not event.tickets:
        missing_fields.append("tickets")

    # --- VALIDAZIONI BUSINESS ---
    validation_errors = validate_event(event)

    # --- STATUS ---
    if missing_fields:
        status = "INCOMPLETE"
    elif validation_errors:
        status = "INVALID"
    else:
        status = "READY"

    return {
        "status": status,
        "missing_fields": missing_fields,
        "validation_errors": validation_errors
    }
