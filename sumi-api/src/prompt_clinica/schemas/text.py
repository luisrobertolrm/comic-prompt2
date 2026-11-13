from pydantic import BaseModel, Field


class TextIn(BaseModel):
    text: str = Field(min_length=3, max_length=4000)


class TextOut(BaseModel):
    text: str
