"""Sets for deduplication."""

from typing import Set

query_set: Set[str] = set()
article_set: Set[str] = set()


def dedup_query(query: str) -> bool:
    """Deduplicate query."""
    if query in query_set:
        return False
    query_set.add(query)
    return True


def dedup_article(article: str) -> bool:
    """Deduplicate article."""
    if article in article_set:
        return False
    article_set.add(article)
    return True
