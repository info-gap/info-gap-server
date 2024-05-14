"""Model of the application."""

from pydantic import BaseModel, Field


class Search(BaseModel):
    """Model of a single search query."""

    query: str = Field(..., description="The search query.")


class Proof(BaseModel):
    """Model of a proof of relevancy."""

    title: str = Field(
        ...,
        description="Title of the article.",
    )
    language_name: str = Field(
        ...,
        description="Name of the proposed programming language. Leave empty if not proposed.",
    )
    purpose: str = Field(
        ...,
        description="Purpose of the proposed programming language.",
    )


class AntiProof(BaseModel):
    """Model of a proof of relevancy."""

    title: str = Field(
        ...,
        description="Title of the article.",
    )
    reason: str = Field(
        ...,
        description="Reason why the article is not relevant.",
    )
