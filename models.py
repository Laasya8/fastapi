from pydantic import BaseModel

class WebhookCreate(BaseModel):
    url: str
    event_type: str
    is_active: bool = True

class WebhookResponse(BaseModel):
    url: str
    event_type: str

class WebhookUpdate(BaseModel):
    url: str
    event_type: str
    is_active: bool


class EventCreate(BaseModel):
    event_type: str
    payload: dict