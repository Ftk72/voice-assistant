from pydantic import BaseModel


class PersonaRef(BaseModel):
    nom: str
    voix: str


class CreerConversation(BaseModel):
    persona: str | None = None


class TourIn(BaseModel):
    texte: str


class DerogationVoix(BaseModel):
    # Voix qui déroge à celle du persona pour la conversation en cours ; effet
    # au tour suivant (ADR 0012 décision 5).
    voix: str


class Interruption(BaseModel):
    # Le préfixe réellement prononcé par le transport avant coupure (ADR 0012
    # décision 3). Vide si rien n'a été entendu.
    prefixe: str = ""


class ConversationVue(BaseModel):
    id: str
    persona: str
    historique: list[dict]


class PreferenceIn(BaseModel):
    # Préférence permanente (réglage grand public, ticket wayfinder 0014).
    persona: str
    voix: str | None = None
