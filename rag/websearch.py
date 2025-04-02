from duckduckgo_search import DDGS
from typing import List

def search_web(query, max_results=5):
    with DDGS() as ddgs:
        results = ddgs.text(query)
        return [
            {"title": r["title"], "body": r["body"], "href": r["href"]}
            for r in results[:max_results]
        ]

def summarize_place_facts(results: List[dict]) -> str:
    # 간단한 요약 템플릿
    facts = []
    for r in results:
        if r["body"]:
            facts.append(f"- {r['body']}")
    return "\n".join(facts[:5])  # 최대 5개 문장

def extract_top_keywords(results: List[dict]) -> List[str]:
    # 단어 카운트 방식 (심플)
    from collections import Counter
    import re

    text = " ".join([r["body"] for r in results if r["body"]])
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    stopwords = {"this", "that", "with", "from", "have", "they", "will", "which", "your"}
    filtered = [w for w in words if w not in stopwords]
    top = Counter(filtered).most_common(3)
    return [w[0] for w in top]
