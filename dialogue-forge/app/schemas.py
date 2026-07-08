from pydantic import BaseModel


class PersonaRef(BaseModel):
    nom: str
    voix: str


class CreerConversation(BaseModel):
    persona: str | None = None


class TourIn(BaseModel):
    texte: str


class Interruption(BaseModel):
    # Le préfixe réellement prononcé par le transport avant coupure (ADR 0012
    # décision 3). Vide si rien n'a été entendu.
    prefixe: str = ""


class ConversationVue(BaseModel):
    id: str
    persona: str
    historique: list[dict]
