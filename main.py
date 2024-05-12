"""Entrypoint of program."""

from typing import List, Iterable, Set, Annotated
import os

from openai import OpenAI
from pydantic import BaseModel, field_validator, Field, BeforeValidator
from instructor.client import Instructor, ChatCompletionMessageParam
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


class Search(BaseModel):
    """Model of a single search query."""

    query: Annotated[
        str,
        BeforeValidator(
            instructor.llm_validator(
                f"The query is formated as: {FORMAT_RULE}",
                client=llm_client,
                model=MODEL,
                allow_override=True,
            )
        ),
    ] = Field(..., description=f"The search query. Format rule is: {FORMAT_RULE}")


def relevant_proof(article: arxiv.Result, request: str):
    """Proof of relevancy of an article to the user request."""

    class _RelevantProof(BaseModel):
        part: Annotated[
            str,
            BeforeValidator(
                instructor.llm_validator(
                    f"""The text must be directly derived from '{article.title}'
                    or '{article.summary}'. It should not be something about other articles!
                    It should also be relevant to '{request}'.""",
                    client=llm_client,
                    model=MODEL,
                    allow_override=False,
                )
            ),
        ] = Field(
            ..., description="Part of article summary that is relevant to user request."
        )
        reason: Annotated[
            str,
            BeforeValidator(
                instructor.llm_validator(
                    f"""The text should explain why paper '{article.title}' is
                    relevant to '{request}' based on '{article.summary}'.
                    It should not be illusionary or irrelevant!""",
                    client=llm_client,
                    model=MODEL,
                    allow_override=False,
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
                raise ValueError("Relevancy should be in the range of 0 to 10")
            return v

    return _RelevantProof


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
                )
                with open("log/query.txt", "a", encoding="UTF-8") as f:
                    f.write(search.model_dump_json(indent=2) + "\n")
                yield search
            except ConnectionError as e:
                print(f'😭 Error: "{e}", retrying!')


class ArticleStream:
    """Generator of articles."""

    searches: Iterable[Search]
    client: arxiv.Client
    generated: Set[str] = set()

    def __init__(self, searches: Iterable[Search], client: arxiv.Client):
        self.searches = searches
        self.client = client

    def iter(self) -> Iterable[arxiv.Result]:
        """Generate articles."""
        for search in self.searches:
            print(f'🔍 Searching for "{search.query}"...')
            try:
                # Search arXiv
                search = arxiv.Search(
                    query=search.query,
                    max_results=10,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                )
                results = self.client.results(search)
                for result in results:
                    # Deduplicate articles by entry_id
                    if result.entry_id not in self.generated:
                        with open("log/article.txt", "a", encoding="UTF-8") as f:
                            f.write(result.title + "\n")
                        self.generated.add(result.entry_id)
                        yield result
            except ConnectionError as e:
                print(f'😭 Error: "{e}", aborting the search!')


class ArticleFeedStream:
    """Generator of article feeds."""

    articles: Iterable[arxiv.Result]
    client: Instructor
    model: str
    request: str

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
            print(f'🔬 Checking if you want to read "{article.title}"...')
            try:
                proof = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.get_history(article),
                    response_model=relevant_proof(article, self.request),
                    max_retries=2,
                )
                feed = ArticleFeed(title=article.title, proof=proof)
                with open("log/feed.txt", "a", encoding="UTF-8") as f:
                    f.write(
                        f"{article.title}\n{feed.proof.model_dump_json(indent=2)}\n\n"
                    )
                yield feed
            except ConnectionError as e:
                print(f'😭 Error: "{e}", aborting the check!')


# Test a stream of search queries
REQUEST = """Can you find me some papers about large language models,
that utilize abstract syntax tree in their research?"""
search_stream = SearchStream(llm_client, MODEL, REQUEST)
article_stream = ArticleStream(search_stream.iter(), arxiv_client)
feed_stream = ArticleFeedStream(article_stream.iter(), llm_client, MODEL, REQUEST)

# Generate feed
for generated_feed in feed_stream.iter():
    pass
