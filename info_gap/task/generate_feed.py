"""Task for generating feed card."""

from typing import Iterable
import re
import arxiv  # type: ignore
from info_gap.config import LOG_PATH
from info_gap.error import ValidationError
from info_gap.model import AntiProof, Proof
from info_gap.task.base_task import BaseTask
from info_gap.task.completion_task import CompletionTask


class GenerateFeedTask(CompletionTask):
    """Task for generating feed card."""

    article: arxiv.Result

    def __init__(self, request: str, article: arxiv.Result):
        self.article = article
        super().__init__(
            name=f"GenerateFeedTask({self.article.title[:30]}...)",
            priority=100,
            request=request,
            temperature=0,
            history=[
                {
                    "role": "system",
                    "content": """You are a world class arXiv paper reader. 
                    Please read the question below, and answer the question 
                    for each requested article.""",
                },
                {
                    "role": "system",
                    "content": """Is this paper about designing a new programming language for LLM?
                    If true, please format your reply as: 'Yes! The name of the programming language is `name`. The language is designed for `purpose`.'
                    Otherwise, please format your reply as: 'No, the paper is not about designing a new programming language for LLM, because `reason`.'""",
                },
                {
                    "role": "user",
                    "content": """Please answer the question for this article:
                    Title: 'LLaMA-3: A Large Language Model for Algebraic Reasoning'
                    Abstract: 'The paper presents LLaMA-3, a large language model for algebraic reasoning.'""",
                },
                {
                    "role": "assistant",
                    "content": """No, the paper is not about designing a new programming language for LLM, because `although it's about LLM, there's no mention of a new programming language.`""",
                },
                {
                    "role": "user",
                    "content": """Please answer the question for this article:
                    Title: 'Rust: a memory-safe programming language'
                    Abstract: 'The paper presents Rust, a memory-safe programming language.'""",
                },
                {
                    "role": "assistant",
                    "content": """No, the paper is not about designing a new programming language for LLM, because `although it's about a programming language, it's not designed for LLM.`""",
                },
                {
                    "role": "user",
                    "content": """Please answer the question for this article:
                    Title: 'XEM-Script: Improving the Security of LLM'
                    Abstract: 'The paper presents XEM-Script, a new programming language that can improve the security of LLM.'""",
                },
                {
                    "role": "assistant",
                    "content": """Yes! The name of the programming language is `XEM-Script`. The language is designed for `improving the security of LLM.`""",
                },
                {
                    "role": "user",
                    "content": f"""Please answer the question for this article:
                    Title: '{article.title}'
                    Abstract: '{article.summary}'""",
                },
            ],
        )

    def parse_response(self, response: str) -> Iterable["BaseTask"]:
        """Parse the response."""
        pattern = r"Yes! The name of the programming language"
        match = re.search(pattern, response)
        if match:
            # Match for programming language
            pattern = r"The name of the programming language is `(.+?)`"
            match = re.search(pattern, response)
            language = ""
            if match:
                language = match.group(1)
            else:
                raise ValidationError(
                    f"Pattern '{pattern}' is not found in your response '{response}'."
                )

            # Match for purpose
            pattern = r"The language is designed for `(.+?)`"
            match = re.search(pattern, response)
            purpose = ""
            if match:
                purpose = match.group(1)
            else:
                raise ValidationError(
                    f"Pattern '{pattern}' is not found in your response '{response}'."
                )

            # Construct proof
            proof = Proof(
                language_name=language, purpose=purpose, title=self.article.title
            )
            with open(f"{LOG_PATH}/proof.txt", "a", encoding="UTF-8") as f:
                f.write(f"{proof.model_dump_json(indent=2)}\n\n")
            yield from []
        else:
            pattern = r"No. the paper is not about"
            match = re.search(pattern, response)
            if not match:
                raise ValidationError(
                    f"'Yes! The name of the programming language' or 'No. the paper is not about' not found in your response '{response}'."
                )

            # Match for reason
            pattern = r"because `(.+?)`"
            match = re.search(pattern, response)
            reason = ""
            if match:
                reason = match.group(1)
            else:
                raise ValidationError(
                    f"Pattern '{pattern}' is not found in your response '{response}'."
                )

            # Construct anti-proof
            anti_proof = AntiProof(reason=reason, title=self.article.title)
            with open(f"{LOG_PATH}/anti_proof.txt", "a", encoding="UTF-8") as f:
                f.write(f"{anti_proof.model_dump_json(indent=2)}\n\n")
