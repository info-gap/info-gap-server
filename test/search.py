"""Test arXiv search."""

import logging
import arxiv  # type: ignore

logging.basicConfig(level=logging.DEBUG)

arxiv_client = arxiv.Client()
search = arxiv.Search(
    query='"large language model" AND "abstract syntax tree"',
    max_results=10,
    sort_by=arxiv.SortCriterion.SubmittedDate,
)
results = arxiv_client.results(search)
for result in results:
    print(result.title)
