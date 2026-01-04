from typing import Optional, List
from pydantic import BaseModel, Field

class Ticket(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    currency: str = "EUR"

class Venue(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None

class EventPreview(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = Field(
        None, description="YYYY-MM-DD"
    )
    venue: Optional[Venue] = None
    tickets: List[Ticket] = []
