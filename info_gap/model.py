"""Model of the application."""

from typing import List
from pydantic import BaseModel, Field
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam


class Example(BaseModel):
    """Model of an example."""

    title: str = Field(
        ...,
        description="The title of the paper.",
    )
    summary: str = Field(
        ...,
        description="The summary of the paper.",
    )
    accepted: bool = Field(
        ...,
        description="Whether the paper is accepted.",
    )
    reason: str = Field(
        ...,
        description="The reason for accept status.",
    )

    def to_message(self) -> List[ChatCompletionMessageParam]:
        """Convert the example to a chat completion message param."""
        return [
            {
                "role": "user",
                "content": f"""Please answer the question for this article: Title: '{self.title}' Abstract: '{self.summary}'""",
            },
            {
                "role": "assistant",
                "content": f"""{'Yes!' if self.accepted else 'No!'} {self.reason}""",
            },
        ]


class Request(BaseModel):
    """Model of the request."""

    this_paper_should_be: str = Field(
        ...,
        description="This paper should be ...",
    )
    accepted_reason_format: str = Field(
        ...,
        description="The format of the true answer.",
    )
    unaccepted_reason_format: str = Field(
        ...,
        description="The format of the otherwise answer.",
    )
    examples: List[Example] = Field(
        ...,
        description="Examples of the question and answer.",
    )


class Search(BaseModel):
    """Model of a single search query."""

    query: str = Field(..., description="The search query.")


class Proof(BaseModel):
    """Model of a proof of relevancy."""

    title: str = Field(
        ...,
        description="Title of the article.",
    )
    reason: str = Field(
        ...,
        description="Reason for relevancy or non-relevancy.",
    )
