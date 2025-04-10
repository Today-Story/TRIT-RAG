from duckduckgo_search import DDGS
from typing import List
from collections import Counter
import re

def search_web(query: str, max_results: int = 5) -> List[dict]:
    """
    DuckDuckGo 검색을 통해 쿼리에 대한 웹 결과 반환
    """
    with DDGS() as ddgs:
        results = ddgs.text(query)
        return [
            {"title": r["title"], "body": r["body"], "href": r["href"]}
            for r in results[:max_results]
        ]

def summarize_place_facts(results: List[dict]) -> str:
    """
    검색 결과를 간단한 리스트 형식으로 요약
    """
    facts = []
    for r in results:
        if r["body"]:
            facts.append(f"- {r['body']}")
    return "\n".join(facts[:5])  # 최대 5줄 요약

def extract_top_keywords(results: List[dict]) -> List[str]:
    """
    검색 결과에서 가장 자주 등장하는 키워드 3개 추출
    """
    text = " ".join([r["body"] for r in results if r["body"]])
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    stopwords = {"this", "that", "with", "from", "have", "they", "will", "which", "your"}
    filtered = [w for w in words if w not in stopwords]
    top = Counter(filtered).most_common(3)
    return [w[0] for w in top]
