from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Iterable
from instructor.client import Instructor

import instructor
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Ollama client
client = instructor.from_openai(
    OpenAI(
        base_url="https://api.openai.com/v1",
        api_key="ollama",  # required, but unused
    ),
    mode=instructor.Mode.JSON,
)

# Model of a single search query
class Search(BaseModel):
    query: str = Field(..., description="The search query")

# Generator of search queries
class SearchStream:
    client: Instructor
    model: str
    request: str
    generated: List[Search] = []

    def __init__(self, client: Instructor, model: str, request: str):
        self.client = client
        self.model = model
        self.request = request

    def get_history(self) -> List[dict]:
        return [
            {
                "role": "system",
                "content": "You are a search agent. Your task is to generate as many search queries as possible, to find information about the user request. Try your best to be creative!",
            },
            {
                "role": "user",
                "content": self.request,
            },
        ]
    
    def iter(self) -> Iterable[Search]:
        while True:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=self.get_history(),
                response_model=Iterable[Search],
            )
            for x in resp:
                # Deduplicate queries
                if x not in self.generated:
                    self.generated.append(x)
                    yield x

# Test a stream of search queries
stream = SearchStream(client, "llama3", "Tell me about the Harry Potter")
for search in stream.iter():
    # Write query to file
    with open("queries.txt", "a") as f:
        f.write(search.query + "\n")