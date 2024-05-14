"""Configuration for OpenAI and arXiv APIs."""

import os
import time
from openai import OpenAI
import instructor
import arxiv  # type: ignore
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize Ollama client
MODEL = "llama3"
LLM_OPENAI = OpenAI(
    base_url=os.getenv("OPENAI_API_URL", "https://api.openai.com/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "sk_1234567890abcdef1234567890abcdef"),
)
LLM_CLIENT = instructor.from_openai(
    LLM_OPENAI,
    mode=instructor.Mode.JSON,
)

# Initialize log path
CURRENT_DATETIME = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
LOG_PATH = f"log/{CURRENT_DATETIME}"
os.makedirs(LOG_PATH, exist_ok=True)

# Initialize arXiv client
ARXIV_CLIENT = arxiv.Client()
QUERY_RULE = """
If you want to find paper about `Keyword One`, your query is: `"Keyword One"`;
If you want to find paper about `Keyword One` AND `Keyword Two`, your query is: `"Keyword One" AND "Keyword Two"`; 
If you want to find paper about `Keyword One` OR `Keyword Two`, your query is: `"Keyword One" OR "Keyword Two"`; 
If you want to find paper about `Keyword One` ANDNOT `Keyword Two`, your query is: `"Keyword One" ANDNOT "Keyword Two"`. 
You can use parenthesis to group the queries!
Keywords should be concise and relevant to the topic you are interested in, 
typically a single word or a short phrase.
"""
MAX_RESULTS = 100
