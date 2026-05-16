import re

import requests
from tools.toolkit import Tool

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _html_to_text(html_fragment: str) -> str:
    clean = re.sub(r'<[^>]+>', '', html_fragment)
    clean = clean.replace('&#x27;', "'").replace('&amp;', '&').replace('&quot;', '"')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:300]


def search_web(query: str) -> str:
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=_HEADERS,
            timeout=15,
        )

        if resp.status_code != 200:
            return f"Error en búsqueda: HTTP {resp.status_code}"

        html = resp.text

        result_blocks = re.findall(
            r'<a rel="nofollow" class="result__a"[^>]*>.*?</a>'
            r'.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html,
            re.DOTALL,
        )

        if not result_blocks:
            snippets = re.findall(
                r'class="result__snippet"[^>]*>(.*?)</a>',
                html,
                re.DOTALL,
            )
            result_blocks = snippets

        if not result_blocks:
            return "No se encontraron resultados."

        seen: set[str] = set()
        results: list[str] = []
        for block in result_blocks:
            text = _html_to_text(block)
            if text and text not in seen:
                seen.add(text)
                results.append(text)
            if len(results) >= 5:
                break

        if not results:
            return "No se encontraron resultados."

        return "\n\n".join(results)

    except requests.Timeout:
        return "La búsqueda tardó demasiado."
    except Exception as e:
        return f"Error en búsqueda: {e}"


def create_web_search_tool() -> Tool:
    return Tool(
        name="web_search",
        description="Busca información actualizada en internet.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta de búsqueda"
                }
            },
            "required": ["query"]
        },
        handler=lambda query: search_web(query)
    )
