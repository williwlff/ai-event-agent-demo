from datetime import date
from typing import List
from models.event import EventPreview

def validate_event(event: EventPreview) -> List[str]:
    errors = []

    if event.date:
        try:
            y, m, d = map(int, event.date.split("-"))
            if date(y, m, d) < date.today():
                errors.append("La data dell'evento è nel passato")
        except Exception:
            errors.append("Formato data non valido")

    if not event.tickets:
        errors.append("Nessuna tipologia di biglietto definita")

    return errors
