from models.event import EventPreview


def render_event_preview(event: EventPreview) -> dict:
    """
    Ritorna una preview strutturata e pronta per UI / API.
    """

    return {
        "title": event.name,
        "date": event.date,
        "location": {
            "address": event.venue.address if event.venue else None,
            "city": event.venue.city if event.venue else None,
        },
        "tickets": [
            {
                "label": t.name,
                "price": f"{t.price:.2f} {t.currency}"
            }
            for t in event.tickets
        ]
    }

def render_event_preview_text(event: EventPreview) -> str:
    """
    Ritorna una preview testuale leggibile per l'utente.
    """

    lines = []

    lines.append(f"🎶 **{event.name}**")

    if event.date:
        lines.append(f"📅 Data: {event.date}")

    if event.venue:
        lines.append(
            f"📍 Luogo: {event.venue.address}, {event.venue.city}"
        )

    if event.tickets:
        lines.append("🎟️ Biglietti:")
        for t in event.tickets:
            lines.append(f"  - {t.name}: {t.price:.2f} {t.currency}")

    return "\n".join(lines)
