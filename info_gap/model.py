"""Model of the application."""

from typing import Annotated
from pydantic import BaseModel, field_validator, Field, BeforeValidator
import instructor
import arxiv  # type: ignore
from info_gap.config import LLM_CLIENT, MODEL, FORMAT_RULE


class Search(BaseModel):
    """Model of a single search query."""

    query: Annotated[
        str,
        BeforeValidator(
            instructor.llm_validator(
                f"The query is formated as: '{FORMAT_RULE}'",
                client=LLM_CLIENT,
                model=MODEL,
                allow_override=True,
                temperature=0,
            )
        ),
    ] = Field(..., description=f"The search query. Format rule is: '{FORMAT_RULE}'")


def relevant_proof(article: arxiv.Result, request: str):
    """Proof of relevancy of an article to the user request."""

    class RelevantProof(BaseModel):
        """Model of a proof of relevancy."""

        part: Annotated[
            str,
            BeforeValidator(
                instructor.llm_validator(
                    f"""The text must be cited from '{article.summary}'!
                    It should not be illusionary or irrelevant!""",
                    client=LLM_CLIENT,
                    model=MODEL,
                    allow_override=False,
                    temperature=0,
                )
            ),
        ] = Field(..., description="Cite relevant part from article summary.")
        reason: Annotated[
            str,
            BeforeValidator(
                instructor.llm_validator(
                    f"""The text should explain why paper '{article.title}' is
                    relevant to request '{request}' based on '{article.summary}'.
                    It should not be illusionary or irrelevant!""",
                    client=LLM_CLIENT,
                    model=MODEL,
                    allow_override=False,
                    temperature=0,
                )
            ),
        ] = Field(..., description="Explain the relevancy.")
        relevancy: float = Field(
            ..., description="Your rating of the relevancy from 0 to 10."
        )

        @field_validator("relevancy")
        @classmethod
        def relevancy_should_be_in_range(cls, v: float) -> float:
            """Check if relevancy is in the range of 0 to 10."""
            if v < 0 or v > 10:
                raise ValueError("Relevancy should be in the range of 0 to 10.")
            return v

    return RelevantProof


class ArticleFeed(BaseModel):
    """Model of an article feed."""

    title: str
    proof: BaseModel
