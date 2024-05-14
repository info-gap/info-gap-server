"""Task for generating feed card."""

from typing import Iterable
import re
import arxiv  # type: ignore
from info_gap.config import LOG_PATH
from info_gap.error import ValidationError
from info_gap.model import Proof, Request
from info_gap.task.base_task import BaseTask
from info_gap.task.completion_task import CompletionTask


class GenerateFeedTask(CompletionTask):
    """Task for generating feed card."""

    request: Request
    article: arxiv.Result

    def __init__(self, request: Request, article: arxiv.Result):
        self.request = request
        self.article = article
        super().__init__(
            name=f"GenerateFeedTask({self.article.title})",
            priority=100,
            temperature=0,
            history=[
                {
                    "role": "system",
                    "content": """You are a world class arXiv paper reader. Please read the question below, and answer the question for each requested article.""",
                },
                {
                    "role": "system",
                    "content": f"""Is this paper {request.this_paper_should_be}? If true, please format your reply as: 'Yes! {request.accepted_reason_format}' Otherwise, please format your reply as: 'No! {request.unaccepted_reason_format}'""",
                },
                # Read examples
                *[
                    message
                    for example in request.examples
                    for message in example.to_message()
                ],
                {
                    "role": "user",
                    "content": f"""Please answer the question for this article: Title: '{article.title}' Abstract: '{article.summary}'""",
                },
            ],
        )

    def parse_response(self, response: str) -> Iterable["BaseTask"]:
        """Parse the response."""
        pattern = r"Yes! (.+)"
        match = re.match(pattern, response)

        # Attempt to match `Yes!` first
        if match:
            reason = match.group(1)
            proof = Proof(reason=reason, title=self.article.title)
            with open(f"{LOG_PATH}/proof.txt", "a", encoding="UTF-8") as f:
                f.write(f"{proof.model_dump_json(indent=2)}\n\n")
            yield from []
        else:
            pattern = r"No! (.+)"
            match = re.match(pattern, response)

            # If not, attempt to match `No!`
            if match:
                reason = match.group(1)
                proof = Proof(reason=reason, title=self.article.title)
                with open(f"{LOG_PATH}/anti-proof.txt", "a", encoding="UTF-8") as f:
                    f.write(f"{proof.model_dump_json(indent=2)}\n\n")
                yield from []
            else:
                raise ValidationError(
                    f"Your response '{response}' does not start with 'Yes!' or 'No!'."
                )
