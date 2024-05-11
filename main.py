from openai import OpenAI
from pydantic import BaseModel, field_validator, Field, BeforeValidator
from typing import List, Iterable, Set, Optional, Annotated
from instructor.client import Instructor
from dotenv import load_dotenv

import instructor
import arxiv
import os

# Load environment
load_dotenv()

# Initialize Ollama client
model = "llama3"
llm_client = instructor.from_openai(
    OpenAI(
        base_url=os.getenv("OPENAI_API_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk_1234567890abcdef1234567890abcdef"),
    ),
    mode=instructor.Mode.JSON,
)

# Initialize arXiv client
arxiv_client = arxiv.Client()

# Model of a single search query
format_rule = "If you want to find paper about `Keyword One`, your query is: `Keyword One`; If you want to find paper about `Keyword One` AND `Keyword Two`, your query is: `Keyword One AND Keyword Two`; If you want to find paper about `Keyword One` OR `Keyword Two`, your query is: `Keyword One OR Keyword Two`; If you want to find paper about `Keyword One` ANDNOT `Keyword Two`, your query is: `Keyword One ANDNOT Keyword Two`. You can use parenthesis to group the query!"
class Search(BaseModel):
    query: Annotated[str, BeforeValidator(instructor.llm_validator(
        f"The query is formated as: {format_rule}", 
        client=llm_client, 
        model=model, 
        allow_override=True
    ))] = Field(..., description=f"The search query. Format rule is: {format_rule}")

# Proof of relevancy of an article to the user request
def RelevantProof(article: arxiv.Result, request: str):
    class RelevantProof(BaseModel):
        part: Annotated[str, BeforeValidator(instructor.llm_validator(
            f"The text must be directly derived from '{article.title}' or '{article.summary}'. It should not be something about other articles! It should also be relevant to '{request}'.", 
            client=llm_client, 
            model=model, 
            allow_override=False
        ))] = Field(..., description="Part of article summary that is relevant to user request.")
        reason: Annotated[str, BeforeValidator(instructor.llm_validator(
            f"The text should explain why paper '{article.title}' is relevant to '{request}' based on '{article.summary}'. It should not be illusionary or irrelevant!", 
            client=llm_client, 
            model=model, 
            allow_override=False
        ))] = Field(..., description="Explain the relevancy.")
        relevancy: float = Field(..., description="Your rating of the relevancy from 0 to 10.")
        
        @field_validator('relevancy')
        @classmethod
        def relevancy_should_be_in_range(cls, v: float) -> float:
            if v < 0 or v > 10:
                raise ValueError("Relevancy should be in the range of 0 to 10")
            return v
    return RelevantProof
    
# Model of an article feed
class ArticleFeed(BaseModel):
    title: str
    proof: BaseModel

# Generator of search queries
class SearchStream:
    client: Instructor
    model: str
    request: str

    def __init__(self, client: Instructor, model: str, request: str):
        self.client = client
        self.model = model
        self.request = request

    def get_history(self) -> List[dict]:
        return [
            {
                "role": "system",
                "content": "You are a world class arXiv search agent. Read the user request and formulate a search query.",
            },
            {
                "role": "user",
                "content": self.request,
            },
        ]
    
    def iter(self) -> Iterable[Search]:
        while True:
            print('🔥 Generating search ideas...')
            try:
                search = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.get_history(),
                    response_model=Search,
                    max_retries=2,
                )
                with open("log/query.txt", "a") as f:
                    f.write(search.model_dump_json(indent=2) + "\n")
                yield search
            except Exception as e:
                print(f'😭 Error: "{e}", retrying!')

# Generator of article
class ArticleStream:
    searches: SearchStream
    client: arxiv.Client
    generated: Set[str] = []

    def __init__(self, searches: SearchStream, client: arxiv.Client):
        self.searches = searches
        self.client = client

    def iter(self) -> Iterable[arxiv.Result]:
        for search in self.searches.iter():
            print(f'🔍 Searching for "{search.query}"...')
            try:
                # Search arXiv
                search = arxiv.Search(
                    query=search.query,
                    max_results=10,
                    sort_by = arxiv.SortCriterion.SubmittedDate
                )
                results = self.client.results(search)
                for result in results:
                    # Deduplicate articles by entry_id
                    if result.entry_id not in self.generated:
                        with open("log/article.txt", "a") as f:
                            f.write(result.title + "\n")
                        self.generated.append(result.entry_id)
                        yield result
            except Exception as e:
                print(f'😭 Error: "{e}", aborting the search!')
                

# Generator of article feed
class ArticleFeedStream:
    articles: ArticleStream
    client: Instructor
    model: str
    request: str

    def __init__(self, articles: ArticleStream, client: Instructor, model: str, request: str):
        self.articles = articles
        self.client = client
        self.model = model
        self.request = request

    def get_history(self, article: arxiv.Result) -> List[dict]:
        return [
            {
                "role": "system",
                "content": f"You are a world class arXiv paper discriminator. Rate the relevancy of the article to the user request. Title: '{article.title}'; Abstract: '{article.summary}'.",
            },
            {
                "role": "user",
                "content": self.request,
            },
        ]

    def iter(self) -> Iterable[ArticleFeed]:
        for article in self.articles.iter():
            print(f'🔬 Checking if you want to read "{article.title}"...')
            try:
                proof = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.get_history(article),
                    response_model=RelevantProof(article, self.request),
                    max_retries=2,
                )
                feed = ArticleFeed(title=article.title, proof=proof)
                with open("log/feed.txt", "a") as f:
                    f.write(f"{article.title}\n{feed.proof.model_dump_json(indent=2)}\n\n")
                yield feed
            except Exception as e:
                print(f'😭 Error: "{e}", aborting the check!')

# Test a stream of search queries
request = "Can you find me some papers about large language models, that utilize abstract syntax tree in their research?"
search_stream = SearchStream(llm_client, model, request)
article_stream = ArticleStream(search_stream, arxiv_client)
feed_stream = ArticleFeedStream(article_stream, llm_client, model, request)

# Generate feed
for feed in feed_stream.iter():
    pass