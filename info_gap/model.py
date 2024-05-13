"""Model of the application."""

from typing import Annotated, Callable
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
import instructor
from instructor import Instructor
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
    ] = Field(..., description="The search query.")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": '"Quantum Computing" AND "Machine Learning"',
                },
                {
                    "query": '("Quantum" OR "Electron") AND ("Machine Learning" OR "LLM")',
                },
                {
                    "query": '("Health" OR "WHO") ANDNOT "COVID-19"',
                },
            ]
        }
    )


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
        relation: str = Field(
            ...,
            description="Relation between the language and LLM.",
        )
        model_config = ConfigDict(
            json_schema_extra={
                "examples": [
                    {
                        "language_name": "",
                        "relation": """Although the article is about LLM, 
                        there is no mention of a programming language.""",
                    },
                    {
                        "language_name": "PythonPlus",
                        "relation": "PythonPlus helps LLM to generate more accurate results.",
                    },
                    {
                        "language_name": "RLHF-Script",
                        "relation": """RLHF-Script is a new programming language that helps 
                        with the training of LLMs.""",
                    },
                ]
            }
        )

    return Proof


class ArticleFeed(BaseModel):
    """Model of an article feed."""

    title: str
    proof: BaseModel
