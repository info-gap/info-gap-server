"""Task for brainstorming search query."""

from typing import Iterable, List
from instructor.client import ChatCompletionMessageParam
from info_gap.task.base_task import BaseTask
from info_gap.task.search import SearchTask
from info_gap.model import Search
from info_gap.config import LOG_PATH, LLM_CLIENT, MODEL, FORMAT_RULE
from info_gap.deduplicate import dedup_query


class BrainStormTask(BaseTask):
    """Task for brainstorming search query."""

    request: str
    priority: int = 32

    def __init__(self, request: str):
        self.request = request

    def get_name(self) -> str:
        """Get the name of the task."""
        return "BrainStormTask"

    def get_history(self) -> List[ChatCompletionMessageParam]:
        """Get the history of the conversation."""
        return [
            {
                "role": "system",
                "content": f"""You are a world class arXiv search agent.
                Read the user request and formulate a search query.
                Please format your query as: '{FORMAT_RULE}'.""",
            },
            {
                "role": "user",
                "content": self.request,
            },
        ]

    def get_priority(self) -> int:
        """Get the priority of the task."""
        return 1

    def run(self) -> Iterable["BaseTask"]:
        """Run the task, return subtasks it generates."""
        try:
            search = LLM_CLIENT.chat.completions.create(
                model=MODEL,
                messages=self.get_history(),
                response_model=Search,
                max_retries=2,
                temperature=1,  # We want the search query to be imaginative
            )

            # Deduplicate the search query
            if dedup_query(search.query):
                with open(f"{LOG_PATH}/query.txt", "a", encoding="UTF-8") as f:
                    f.write(search.model_dump_json(indent=2) + "\n")
                yield SearchTask(request=self.request, search=search)
        finally:
            # For every 4 articles searched, we brainstorm a new search query
            self.priority -= 4
            yield self
