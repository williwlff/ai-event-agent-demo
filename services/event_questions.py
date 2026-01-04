from typing import Optional
from models.event import EventPreview


def next_missing_question(event: EventPreview) -> Optional[str]:
    """
    Ritorna la prossima domanda da fare all'utente
    in base ai campi mancanti.
    """

    # 1️⃣ Nome evento
    if not event.name:
        return "Qual è il nome dell’evento?"

    # 2️⃣ Data evento
    if not event.date:
        return "In che data si terrà l’evento?"

    # 3️⃣ Venue
    if not event.venue:
        return "Dove si terrà l’evento? (indirizzo e città)"

    if not event.venue.address:
        return "Qual è l’indirizzo dell’evento?"

    if not event.venue.city:
        return "In quale città si terrà l’evento?"

    # 4️⃣ Biglietti
    if not event.tickets:
        return (
            "Quali tipologie di biglietti sono previste "
            "e a che prezzo?"
        )

    # 👉 tutto completo
    return None
