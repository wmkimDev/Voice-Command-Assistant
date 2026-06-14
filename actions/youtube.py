from __future__ import annotations

from urllib.parse import quote_plus

from actions.browser import navigate_current_tab, navigate_url, open_new_url


def youtube_search(query: str) -> dict[str, object]:
    return _youtube_search(query, mode="existing")


def youtube_search_new_tab(query: str) -> dict[str, object]:
    return _youtube_search(query, mode="new")


def youtube_search_current_tab(query: str) -> dict[str, object]:
    return _youtube_search(query, mode="current")


def _youtube_search(query: str, mode: str) -> dict[str, object]:
    encoded = quote_plus(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    if mode == "new":
        return open_new_url(url, action="youtube_search_new_tab")
    if mode == "current":
        return navigate_current_tab(url, action="youtube_search_current_tab")
    return navigate_url(url, action="youtube_search")
