from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Source = Literal["conversation", "document"]


class EpisodeIn(BaseModel):
    """Unité d'ingestion : un échange de conversation daté ou un fragment de document."""

    content: str
    source: Source
    name: str


class Provenance(BaseModel):
    source: Source
    name: str


class Fact(BaseModel):
    """Une relation mémorisée, avec provenance et période de validité (cf. CONTEXT.md)."""

    text: str
    provenance: Provenance
    valid_at: datetime | None = None
    invalid_at: datetime | None = None


class SearchResponse(BaseModel):
    facts: list[Fact]
