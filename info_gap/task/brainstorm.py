"""Task for brainstorming search query."""

from typing import Iterable
import re
from info_gap.error import ValidationError
from info_gap.task.base_task import BaseTask
from info_gap.task.completion_task import CompletionTask
from info_gap.task.search import SearchTask
from info_gap.model import Request, Search
from info_gap.config import LOG_PATH, QUERY_RULE
from info_gap.deduplicate import dedup_query


class BrainStormTask(CompletionTask):
    """Task for brainstorming search query."""

    request: Request

    def __init__(self, request: Request):
        self.request = request
        super().__init__(
            name="BrainStormTask",
            priority=32,
            temperature=1,
            history=[
                {
                    "role": "system",
                    "content": """You are a world class arXiv search agent. Read the user request and formulate a search query.""",
                },
                {
                    "role": "system",
                    "content": f"""The rule for a search query is: '{QUERY_RULE}'""",
                },
                {
                    "role": "system",
                    "content": """Please format your reply STRICTLY as: 'Sure! I want to search with keyword `your_keyword`.'""",
                },
                {
                    "role": "user",
                    "content": "Can you find me some papers about quantum computing?",
                },
                {
                    "role": "assistant",
                    "content": """Sure! I want to search with keyword `"quantum compute" OR "quantum computing"`.""",
                },
                {
                    "role": "user",
                    "content": "Can you find me some papers about COVID-19?",
                },
                {
                    "role": "assistant",
                    "content": """Sure! I want to search with keyword `"COVID-19" AND "virus"`.""",
                },
                {
                    "role": "user",
                    "content": "Can you find me some papers about RLHF in image generation?",
                },
                {
                    "role": "assistant",
                    "content": """Sure! I want to search with keyword `("RLHF" AND "image generation") ANDNOT "NLP"`.""",
                },
                {
                    "role": "user",
                    "content": f"""Can you find me some papers {self.request.this_paper_should_be}?""",
                },
                {
                    "role": "assistant",
                    "content": """Sure! I want to """,
                },
            ],
        )

    def parse_response(self, response: str) -> Iterable["BaseTask"]:
        """Parse the response."""
        pattern = r"search with keyword `(.+?)`"
        match = re.search(pattern, response)
        if match:
            query = match.group(1)
            search = Search(query=query)
            if dedup_query(search.query):
                with open(f"{LOG_PATH}/query.txt", "a", encoding="UTF-8") as f:
                    f.write(search.model_dump_json(indent=2) + "\n")

                # For every 4 articles searched, we brainstorm a new search query.
                self.priority -= 4
                yield SearchTask(request=self.request, search=search)
        else:
            raise ValidationError(
                f"""Pattern '{pattern}' is not found in your response '{response}'."""
            )

    def after_run(self) -> Iterable[BaseTask]:
        """After run, add another brainstorm as subtask."""
        yield self
