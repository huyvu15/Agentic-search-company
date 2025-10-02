from ddgs import DDGS
from playwright.sync_api import sync_playwright
import trafilatura
from typing import List, Dict, Optional

def search_internet(query: str, max_results: int = 5, request_timeout_ms: int = 20000) -> List[Dict[str, Optional[str]]]:
    results = list(DDGS().text(query, max_results=max_results)) 
    extracted: List[Dict[str, Optional[str]]] = []

    def get_page_text(url: str) -> Optional[str]:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.goto(url, timeout=request_timeout_ms)
                    html = page.content()
                    page.close()
                finally:
                    browser.close()
                return trafilatura.extract(html)
        except Exception:
            return None  

    for r in results:
        url = r.get("href")
        title = r.get("title")
        content = get_page_text(url) if url else None
        extracted.append({"title": title, "url": url, "content": content})

    return extracted

if __name__ == "__main__":
    items = search_internet("Công ty mobiwork")
    print(items)