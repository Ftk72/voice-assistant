from pydantic import BaseModel


class PersonaRef(BaseModel):
    nom: str
    voix: str


class CreerConversation(BaseModel):
    persona: str | None = None


class TourIn(BaseModel):
    texte: str


class ConversationVue(BaseModel):
    id: str
    persona: str
    historique: list[dict]
