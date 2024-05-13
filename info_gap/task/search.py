"""Task for running search query."""

from typing import Iterable, Generator, Optional
import arxiv  # type: ignore
from info_gap.model import Search
from info_gap.task.base_task import BaseTask
from info_gap.task.generate_feed import GenerateFeedTask
from info_gap.config import LOG_PATH, ARXIV_CLIENT
from info_gap.deduplicate import dedup_article


class SearchTask(BaseTask):
    """Task for running search query."""

    request: str
    search: Search
    priority: int = 36

    result_generator: Optional[Generator[arxiv.Result, None, None]]

    def __init__(self, request: str, search: Search):
        self.request = request
        self.search = search
        self.result_generator = None

    def get_name(self) -> str:
        """Get the name of the task."""
        return f"SearchTask({self.search.query[:30]}...)"

    def get_priority(self) -> int:
        """Get the priority of the task. New articles are favored."""
        return self.priority

    def init_generator(self):
        """Initialize the generator for search results."""
        arxiv_search = arxiv.Search(
            query=self.search.query,
            max_results=40,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )
        self.result_generator = ARXIV_CLIENT.results(arxiv_search)

    def run(self) -> Iterable["BaseTask"]:
        """Run the task, return subtasks it generates."""
        if self.result_generator is None:
            # Initialize the generator if it is None
            self.init_generator()
            assert self.result_generator is not None
        try:
            # Search and deduplicate the articles
            result = next(self.result_generator)
            if dedup_article(result.entry_id):
                with open(f"{LOG_PATH}/article.txt", "a", encoding="UTF-8") as f:
                    f.write(result.title + "\n")
                yield GenerateFeedTask(request=self.request, article=result)

            # Return lower priority version of `self` as subtask
            self.priority -= 1
            yield self
        except StopIteration:
            yield from []
