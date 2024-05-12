"""Entrypoint of program."""

from typing import List, Iterable, Set, Annotated
import os
import time
import logging

from openai import OpenAI, BadRequestError
from pydantic import BaseModel, field_validator, Field, BeforeValidator
from instructor.client import Instructor, ChatCompletionMessageParam
from instructor.retry import InstructorRetryException  # type: ignore
from dotenv import load_dotenv
import instructor
import arxiv  # type: ignore

# Load environment
load_dotenv()

# Initialize Ollama client
MODEL = "llama3"
llm_client = instructor.from_openai(
    OpenAI(
        base_url=os.getenv("OPENAI_API_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk_1234567890abcdef1234567890abcdef"),
    ),
    mode=instructor.Mode.JSON,
)

# Initialize arXiv client
arxiv_client = arxiv.Client()
FORMAT_RULE = """If you want to find paper about `Keyword One`,
your query is: `Keyword One`; 
If you want to find paper about `Keyword One` AND `Keyword Two`, 
your query is: `Keyword One AND Keyword Two`; 
If you want to find paper about `Keyword One` OR `Keyword Two`, 
your query is: `Keyword One OR Keyword Two`; 
If you want to find paper about `Keyword One` ANDNOT `Keyword Two`, 
your query is: `Keyword One ANDNOT Keyword Two`. 
You can use parenthesis to group the query!"""

# Initialize log path
current_datetime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
log_path = f"log/{current_datetime}"
os.makedirs(log_path, exist_ok=True)

# Redirect debug log to file
logging.basicConfig(
    filename=f"{log_path}/debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class Search(BaseModel):
    """Model of a single search query."""

    query: Annotated[
        str,
        BeforeValidator(
            instructor.llm_validator(
                f"The query is formated as: '{FORMAT_RULE}'",
                client=llm_client,
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
                    client=llm_client,
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
                    client=llm_client,
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


class SearchStream:
    """Generator of search queries."""

    client: Instructor
    model: str
    request: str

    def __init__(self, client: Instructor, model: str, request: str):
        self.client = client
        self.model = model
        self.request = request

    def get_history(self) -> List[ChatCompletionMessageParam]:
        """Get the history of the conversation."""
        return [
            {
                "role": "system",
                "content": """You are a world class arXiv search agent.
                Read the user request and formulate a search query.""",
            },
            {
                "role": "user",
                "content": self.request,
            },
        ]

    def iter(self) -> Iterable[Search]:
        """Generate search queries."""
        while True:
            print("🔥 Generating search ideas...")
            try:
                search = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.get_history(),
                    response_model=Search,
                    max_retries=2,
                    temperature=1,  # We want the search query to be imaginative
                )
                with open(f"{log_path}/query.txt", "a", encoding="UTF-8") as f:
                    f.write(search.model_dump_json(indent=2) + "\n")
                yield search
            except BadRequestError as e:
                print(f'😭 Connection is unstable: "{e}", retrying!')
            except InstructorRetryException as e:
                print(f'😭 Max retry exceeded: "{e}", retrying!')


class ArticleStream:
    """Generator of articles."""

    searches: Iterable[Search]
    client: arxiv.Client

    def __init__(self, searches: Iterable[Search], client: arxiv.Client):
        self.searches = searches
        self.client = client

    def iter(self) -> Iterable[arxiv.Result]:
        """Generate articles."""
        for search in self.searches:
            print(f'🔍 Searching for "{search.query}"...')
            try:
                search = arxiv.Search(
                    query=search.query,
                    max_results=10,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                )
                results = self.client.results(search)
                for result in results:
                    with open(f"{log_path}/article.txt", "a", encoding="UTF-8") as f:
                        f.write(result.title + "\n")
                    yield result
            except ConnectionError as e:
                print(f'😭 Error: "{e}", aborting the search!')


class ArticleFeedStream:
    """Generator of article feeds."""

    articles: Iterable[arxiv.Result]
    client: Instructor
    model: str
    request: str
    checked_article_ids: Set[str] = set()

    def __init__(
        self,
        articles: Iterable[arxiv.Result],
        client: Instructor,
        model: str,
        request: str,
    ):
        self.articles = articles
        self.client = client
        self.model = model
        self.request = request

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

    def iter(self) -> Iterable[ArticleFeed]:
        """Generate article feeds."""
        for article in self.articles:
            # Deduplicate articles
            if article.entry_id in self.checked_article_ids:
                continue

            # Run check if not duplicate
            print(f'🔬 Checking if you want to read "{article.title}"...')
            try:
                proof = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.get_history(article),
                    response_model=relevant_proof(article, self.request),
                    max_retries=2,
                    temperature=0,  # We want the proof to be accurate
                    presence_penalty=-2,  # We want to encourage the proof to be relevant
                )

                # Feed is successfully generated at this point, run deduplication
                self.checked_article_ids.add(article.entry_id)
                feed = ArticleFeed(title=article.title, proof=proof)
                with open(f"{log_path}/feed.txt", "a", encoding="UTF-8") as f:
                    f.write(
                        f"{article.title}\n{feed.proof.model_dump_json(indent=2)}\n\n"
                    )
                yield feed
            except BadRequestError as e:
                print(f'😭 Connection is unstable: "{e}", aborting the check!')
            except InstructorRetryException as e:
                print(f'😭 Max retry exceeded: "{e}", retrying!')

                # Retry exception is typically triggered when the article is irrelevant
                # to the user request, so it's better to deduplicate it
                self.checked_article_ids.add(article.entry_id)


# Test a stream of search queries
REQUEST = """Can you find me some papers about designing a new
programming language for LLM model?"""
search_stream = SearchStream(llm_client, MODEL, REQUEST)
article_stream = ArticleStream(search_stream.iter(), arxiv_client)
feed_stream = ArticleFeedStream(article_stream.iter(), llm_client, MODEL, REQUEST)

# Generate feed
for generated_feed in feed_stream.iter():
    pass
