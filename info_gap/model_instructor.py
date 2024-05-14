"""Model of the application."""

from typing import Annotated, Callable
from pydantic import BaseModel, Field, BeforeValidator
import instructor
from instructor import Instructor
import arxiv  # type: ignore
from info_gap.config import LLM_CLIENT, MODEL, QUERY_RULE


class Search(BaseModel):
    """Model of a single search query."""

    query: Annotated[
        str,
        BeforeValidator(
            instructor.llm_validator(
                f"The query is formated as: '{QUERY_RULE}'",
                client=LLM_CLIENT,
                model=MODEL,
                allow_override=True,
                temperature=0,
            )
        ),
    ] = Field(..., description="The search query.")


def validate_when_nonempty(
    statement: str,
    client: Instructor,
    allow_override: bool = False,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0,
) -> Callable[[str], str]:
    """Validate a string with LLM when it is nonempty."""

    def llm(x: str):
        if x == "":
            return x
        return instructor.llm_validator(
            statement, client, allow_override, model, temperature
        )(x)

    return llm


def relevant_proof(article: arxiv.Result):
    """Proof that the article is relevant to the user request."""

    class Proof(BaseModel):
        """Model of a proof of relevancy."""

        language_name: Annotated[
            str,
            BeforeValidator(
                validate_when_nonempty(
                    f"""It should be part of '{article.summary}',
                    and it should be a programming language,
                    not just a framework or an approach.""",
                    client=LLM_CLIENT,
                    model=MODEL,
                    allow_override=False,
                    temperature=0,
                )
            ),
        ] = Field(
            ...,
            description="Name of the proposed programming language. Leave empty if not proposed.",
        )
        purpose: str = Field(
            ...,
            description="Purpose of the proposed programming language.",
        )

    return Proof


class ArticleFeed(BaseModel):
    """Model of an article feed."""

    title: str
    proof: BaseModel
