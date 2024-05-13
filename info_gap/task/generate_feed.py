"""Task for generating feed card."""

from typing import Iterable, List
import arxiv  # type: ignore
from instructor.client import ChatCompletionMessageParam
from info_gap.model import relevant_proof, ArticleFeed
from info_gap.task.base_task import BaseTask
from info_gap.config import LOG_PATH, LLM_CLIENT, MODEL


class GenerateFeedTask(BaseTask):
    """Task for generating feed card."""

    request: str
    article: arxiv.Result

    def __init__(self, request: str, article: arxiv.Result):
        self.request = request
        self.article = article

    def get_name(self) -> str:
        """Get the name of the task."""
        return f"GenerateFeedTask({self.article.title[:30]}...)"

    def get_history(self, article: arxiv.Result) -> List[ChatCompletionMessageParam]:
        """Get the history of the conversation."""
        return [
            {
                "role": "system",
                "content": f"""You are a world class arXiv paper discriminator. 
                Rate the relevancy of the article to the user request. 
                Title: '{article.title}'; Abstract: '{article.summary}'.""",
            },
            {
                "role": "user",
                "content": self.request,
            },
        ]

    def get_priority(self) -> int:
        """Get the priority of the task."""
        return 100

    def run(self) -> Iterable["BaseTask"]:
        """Run the task, return subtasks it generates."""
        proof = LLM_CLIENT.chat.completions.create(
            model=MODEL,
            messages=self.get_history(self.article),
            response_model=relevant_proof(self.article, self.request),
            max_retries=2,
            temperature=0,  # We want the proof to be accurate
            presence_penalty=-2,  # We want to encourage the proof to be relevant
        )
        feed = ArticleFeed(title=self.article.title, proof=proof)
        with open(f"{LOG_PATH}/feed.txt", "a", encoding="UTF-8") as f:
            f.write(f"{self.article.title}\n{feed.proof.model_dump_json(indent=2)}\n\n")
        yield from []
