from duckduckgo_search import DDGS


def research_competitors(query: str, max_results: int = 5) -> dict:
    """Search the web for competitor or market intelligence."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        return {"error": f"Search failed: {e}", "results": []}

    cleaned = [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in results
    ]

    return {
        "query": query,
        "result_count": len(cleaned),
        "results": cleaned,
    }


TOOL_DEFINITION = {
    "name": "research_competitors",
    "description": (
        "Search the web for competitor analysis, market trends, pricing, or "
        "industry news. Returns titles, URLs, and snippets. Use this when the "
        "user asks about competitors, market positioning, or industry insights."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for competitor or market research.",
            },
            "max_results": {
                "type": "integer",
                "description": "Number of search results to return (default 5).",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}
