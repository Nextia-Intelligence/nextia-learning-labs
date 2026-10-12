"""What the API accepts. FastAPI checks every request against these before any code runs."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=500, description="The question, in plain words.")
    as_of: date | None = Field(default=None, description="The date the answer is for (default: today). "
                                                         "Policies change: the version in force on this date is used.")
