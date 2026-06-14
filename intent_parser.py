from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urlparse

import requests

from config import (
    ALLOWED_ACTIONS,
    OLLAMA_ENDPOINT,
    OLLAMA_MODEL,
    PARSE_TIMEOUT_SECONDS,
    URL_ALIASES,
)

logger = logging.getLogger(__name__)

UNKNOWN_INTENT = {"action": "unknown", "query": None, "url": None}


def parse_intent(transcript: str, timeout: int = PARSE_TIMEOUT_SECONDS) -> dict[str, Any]:
    transcript = transcript.strip()
    if not transcript:
        return UNKNOWN_INTENT.copy()

    local_intent = parse_local_intent(transcript)
    if local_intent is not None:
        return local_intent

    payload = {
        "model": OLLAMA_MODEL,
        "system": build_system_prompt(),
        "prompt": transcript,
        "stream": False,
        "format": "json",
    }

    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.error("Ollama request failed: %s", exc)
        return UNKNOWN_INTENT.copy()
    except json.JSONDecodeError as exc:
        logger.error("Ollama returned invalid response JSON: %s", exc)
        return UNKNOWN_INTENT.copy()

    raw = data.get("response", "")
    try:
        parsed = extract_json_object(raw)
    except ValueError as exc:
        logger.error("Failed to parse intent JSON: %s", exc)
        return UNKNOWN_INTENT.copy()

    return validate_intent(parsed)


def parse_local_intent(transcript: str) -> dict[str, Any] | None:
    normalized = transcript.strip()
    lowered = normalized.lower()

    close_intent = _extract_close_tab_intent(normalized, lowered)
    if close_intent:
        return close_intent

    youtube_intent = _extract_youtube_intent(normalized, lowered)
    if youtube_intent:
        return youtube_intent

    google_intent = _extract_google_intent(normalized, lowered)
    if google_intent:
        return google_intent

    current_url = _extract_current_tab_url(normalized, lowered)
    if current_url:
        return {"action": "open_current_tab", "query": None, "url": current_url}

    if _is_new_tab_command(lowered):
        return {"action": "new_tab", "query": None, "url": None}

    url = _extract_open_tab_url(normalized, lowered)
    if url:
        return {"action": "open_tab", "query": None, "url": url}

    tab_keyword = _extract_focus_tab_keyword(normalized, lowered)
    if tab_keyword:
        return {"action": "focus_tab", "query": tab_keyword, "url": None}

    if _looks_like_unsupported_command(lowered):
        return None

    return {"action": "type_text", "query": normalized, "url": None}


def build_system_prompt() -> str:
    aliases = "\n".join(f"- {name}: {url}" for name, url in sorted(URL_ALIASES.items()))
    return f"""
You are a voice command parser. The user speaks in Korean, English, or a mix of both.
Your job is to parse the user's intent and output ONLY a JSON object. No explanation, no markdown, no other text.

Output schema:
{{"action":"<action_name>","query":"<text or null>","url":"<url or null>"}}

Available actions:
- type_text: type the user's dictated text into the currently focused input. Requires query.
- youtube_search: search YouTube by reusing an existing YouTube tab if available. Requires query.
- youtube_search_new_tab: search YouTube in a new tab. Requires query.
- youtube_search_current_tab: search YouTube in the current Chrome tab. Requires query.
- google_search: search Google by reusing an existing Google tab if available. Requires query.
- google_search_new_tab: search Google in a new tab. Requires query.
- google_search_current_tab: search Google in the current Chrome tab. Requires query.
- chatgpt_ask: put a question into the ChatGPT input box. Requires query. Do not submit.
- open_tab: open or focus a Chrome tab for a URL. Requires url.
- open_current_tab: navigate the current Chrome tab to a URL. Requires url.
- new_tab: open a blank new Chrome tab. Requires no query or url.
- focus_tab: focus an existing Chrome tab by title or URL keyword. Requires query.
- close_current_tab: close the current Chrome tab. Requires no query or url.
- close_tab: close one existing Chrome tab by title or URL keyword. Requires query.
- unknown: use when intent is unclear or unsupported.

Rules:
- Preserve the user's query language exactly. Do not translate.
- Use only http:// or https:// URLs.
- Prefer these URL aliases for open_tab:
{aliases}
- If the user is just dictating text without a command, use type_text.
- If unsure, return unknown.

Examples:
Input: 유튜브에서 고양이 검색해줘
Output: {{"action":"youtube_search","query":"고양이","url":null}}

Input: ChatGPT에 파이썬 정렬 알고리즘 물어봐줘
Output: {{"action":"chatgpt_ask","query":"파이썬 정렬 알고리즘","url":null}}

Input: 쿠팡 탭으로 이동해줘
Output: {{"action":"open_tab","query":null,"url":"https://www.coupang.com"}}

Input: 안녕하세요 반갑습니다
Output: {{"action":"type_text","query":"안녕하세요 반갑습니다","url":null}}

Input: search YouTube for cat videos
Output: {{"action":"youtube_search","query":"cat videos","url":null}}

Input: ask ChatGPT about sorting algorithms in Python
Output: {{"action":"chatgpt_ask","query":"sorting algorithms in Python","url":null}}

Input: go to Coupang
Output: {{"action":"open_tab","query":null,"url":"https://www.coupang.com"}}

Input: 유튜브에서 cat videos 검색해줘
Output: {{"action":"youtube_search","query":"cat videos","url":null}}

Input: 구글에 서울 날씨 검색해줘
Output: {{"action":"google_search","query":"서울 날씨","url":null}}
""".strip()


def extract_json_object(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()

    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        json_text = _find_first_json_object(cleaned)
        if json_text is None:
            raise ValueError("no JSON object found")
        value = json.loads(json_text)

    if not isinstance(value, dict):
        raise ValueError("parsed JSON is not an object")
    return value


def validate_intent(intent: dict[str, Any]) -> dict[str, Any]:
    action = intent.get("action")
    query = intent.get("query")
    url = intent.get("url")

    if action not in ALLOWED_ACTIONS:
        return UNKNOWN_INTENT.copy()

    if query == "":
        query = None
    if url == "":
        url = None

    if action in {
        "type_text",
        "youtube_search",
        "youtube_search_new_tab",
        "youtube_search_current_tab",
        "google_search",
        "google_search_new_tab",
        "google_search_current_tab",
        "chatgpt_ask",
    }:
        if not isinstance(query, str) or not query.strip():
            return UNKNOWN_INTENT.copy()
        return {"action": action, "query": query, "url": None}

    if action == "new_tab":
        return {"action": "new_tab", "query": None, "url": None}

    if action == "focus_tab":
        if not isinstance(query, str) or not query.strip():
            return UNKNOWN_INTENT.copy()
        return {"action": "focus_tab", "query": query.strip(), "url": None}

    if action == "close_current_tab":
        return {"action": "close_current_tab", "query": None, "url": None}

    if action == "close_tab":
        if not isinstance(query, str) or not query.strip():
            return UNKNOWN_INTENT.copy()
        return {"action": "close_tab", "query": query.strip(), "url": None}

    if action in {"open_tab", "open_current_tab"}:
        resolved_url = _resolve_url(url, query)
        if resolved_url is None:
            return UNKNOWN_INTENT.copy()
        return {"action": action, "query": None, "url": resolved_url}

    return UNKNOWN_INTENT.copy()


def _extract_youtube_intent(text: str, lowered: str) -> dict[str, Any] | None:
    query = _extract_youtube_query(text)
    if query is None:
        return None

    if _mentions_current_tab(lowered):
        return {"action": "youtube_search_current_tab", "query": query, "url": None}
    if _mentions_new_tab(lowered):
        return {"action": "youtube_search_new_tab", "query": query, "url": None}
    return {"action": "youtube_search", "query": query, "url": None}


def _extract_close_tab_intent(text: str, lowered: str) -> dict[str, Any] | None:
    close_words = ("닫아", "닫아줘", "닫기", "꺼", "꺼줘", "close")
    if "탭" not in lowered and "tab" not in lowered:
        return None
    if not any(word in lowered for word in close_words):
        return None

    if _mentions_current_tab(lowered):
        return {"action": "close_current_tab", "query": None, "url": None}

    patterns = [
        r"(.+?)\s*탭(?:을|를)?\s*(?:닫아줘|닫아|닫기|꺼줘|꺼)",
        r"(?:close)\s+(.+?)\s+tab",
        r"(.+?)\s+tab\s+(?:close)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            keyword = _clean_tab_keyword(match.group(1))
            if keyword:
                return {"action": "close_tab", "query": keyword, "url": None}

    return None


def _extract_google_intent(text: str, lowered: str) -> dict[str, Any] | None:
    query = _extract_search_query(text, targets=("구글", "google"))
    if query is None:
        return None

    if _mentions_current_tab(lowered):
        return {"action": "google_search_current_tab", "query": query, "url": None}
    if _mentions_new_tab(lowered):
        return {"action": "google_search_new_tab", "query": query, "url": None}
    return {"action": "google_search", "query": query, "url": None}


def _extract_youtube_query(text: str) -> str | None:
    return _extract_search_query(text, targets=("유튜브", "youtube"))


def _extract_search_query(text: str, targets: tuple[str, ...]) -> str | None:
    korean_targets = [target for target in targets if not target.isascii()]
    english_targets = [target for target in targets if target.isascii()]
    korean_target_pattern = "|".join(re.escape(target) for target in korean_targets)
    english_target_pattern = "|".join(re.escape(target) for target in english_targets)
    patterns = []
    if korean_target_pattern:
        patterns.extend(
            [
                rf"(?:새\s*탭(?:에서|으로|을\s*열어서)?\s*)?(?:{korean_target_pattern})(?:에서|에)?\s*(.+?)\s*(?:검색해줘|검색|찾아줘|찾아)",
                rf"(?:현재\s*탭(?:에서|으로)?\s*)?(?:{korean_target_pattern})(?:에서|에)?\s*(.+?)\s*(?:검색해줘|검색|찾아줘|찾아)",
                rf"(?:{korean_target_pattern})(?:에서|에)?\s*(.+?)\s*(?:검색해줘|검색|찾아줘|찾아)",
                rf"(.+?)\s*(?:이라고|라고|이라|라|을|를)?\s*(?:{korean_target_pattern})(?:에서|에)?\s*(?:검색해줘|검색|찾아줘|찾아)",
            ]
        )
    if english_target_pattern:
        patterns.extend(
            [
                rf"(?:search\s+)?(?:{english_target_pattern})\s+(?:for\s+)?(.+)",
            ]
        )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            query = _strip_polite_suffix(match.group(1))
            if query:
                return query
    return None


def _is_new_tab_command(lowered: str) -> bool:
    compact = _compact(lowered)
    korean_match = _mentions_new_tab(lowered) and any(
        word in compact for word in ("열어", "열어줘", "만들어", "만들어줘", "생성")
    )
    english_match = any(
        phrase in lowered
        for phrase in (
            "new tab",
            "blank tab",
            "open a tab",
            "open tab",
        )
    )
    return korean_match or english_match


def _extract_current_tab_url(text: str, lowered: str) -> str | None:
    if not _mentions_current_tab(lowered):
        return None
    if not any(word in lowered for word in ("이동", "이동해줘", "열어", "열어줘", "가줘", "접속", "open", "go to")):
        return None

    for alias, url in sorted(URL_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias.lower() in lowered:
            return url

    url_match = re.search(r"https?://[^\s]+", text)
    if url_match:
        return _resolve_url(url_match.group(0), None)

    return None


def _extract_open_tab_url(text: str, lowered: str) -> str | None:
    open_words = (
        "열어",
        "열어줘",
        "이동",
        "이동해줘",
        "가줘",
        "접속",
        "탭",
        "open",
        "go to",
        "move to",
    )

    if not any(word in lowered for word in open_words):
        return None

    for alias, url in sorted(URL_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias.lower() in lowered:
            return url

    url_match = re.search(r"https?://[^\s]+", text)
    if url_match:
        return _resolve_url(url_match.group(0), None)

    return None


def _mentions_new_tab(lowered: str) -> bool:
    compact = _compact(lowered)
    return any(phrase in compact for phrase in ("새탭", "새로운탭", "빈탭")) or any(
        phrase in lowered for phrase in ("new tab", "blank tab")
    )


def _mentions_current_tab(lowered: str) -> bool:
    compact = _compact(lowered)
    return any(phrase in compact for phrase in ("현재탭", "지금탭", "현재창", "이탭")) or any(
        phrase in lowered for phrase in ("current tab", "this tab")
    )


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _extract_focus_tab_keyword(text: str, lowered: str) -> str | None:
    focus_words = (
        "이동",
        "이동해줘",
        "가줘",
        "찾아줘",
        "찾아",
        "전환",
        "바꿔",
        "switch",
        "focus",
        "go to",
        "move to",
    )
    if "탭" not in lowered and "tab" not in lowered:
        return None
    if not any(word in lowered for word in focus_words):
        return None

    patterns = [
        r"(.+?)\s*탭(?:으로|에)?\s*(?:이동해줘|이동|가줘|찾아줘|찾아|전환|바꿔)",
        r"(?:move to|go to|switch to|focus)\s+(.+?)\s+tab",
        r"(.+?)\s+tab(?:으로)?\s*(?:move|go|switch|focus)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            keyword = _clean_tab_keyword(match.group(1))
            if keyword:
                return keyword

    return None


def _clean_tab_keyword(text: str) -> str:
    cleaned = text.strip().strip('"\'')
    cleaned = re.sub(r"^(저기|그|이|저|the|a|an)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*(으로|로)$", "", cleaned)
    if cleaned in {"새", "새로운", "빈", "new", "blank"}:
        return ""
    return cleaned.strip()


def _looks_like_unsupported_command(lowered: str) -> bool:
    command_words = (
        "삭제",
        "지워",
        "종료",
        "꺼",
        "보내",
        "전송",
        "실행",
        "delete",
        "remove",
        "quit",
        "send",
        "run",
    )
    return any(word in lowered for word in command_words)


def _strip_polite_suffix(text: str) -> str:
    cleaned = text.strip().strip('"\'')
    cleaned = re.sub(r"^(?:새\s*탭(?:에서|으로|을\s*열어서)?|현재\s*탭(?:에서|으로)?|지금\s*탭(?:에서|으로)?)\s*", "", cleaned)
    suffixes = [
        "검색해줘",
        "검색",
        "찾아줘",
        "찾아",
        "해줘",
        "please",
    ]
    for suffix in suffixes:
        lowered = cleaned.lower()
        if lowered.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
    particles = [
        "이라고",
        "라고",
        "이라",
        "라",
        "으로",
        "로",
        "을",
        "를",
    ]
    for particle in particles:
        if cleaned.endswith(particle) and len(cleaned) > len(particle):
            cleaned = cleaned[: -len(particle)].strip()
            break
    return cleaned


def _resolve_url(url: Any, query: Any) -> str | None:
    if isinstance(query, str):
        alias = URL_ALIASES.get(query.strip().lower()) or URL_ALIASES.get(query.strip())
        if alias:
            return alias

    if not isinstance(url, str):
        return None

    stripped = url.strip()
    alias = URL_ALIASES.get(stripped.lower()) or URL_ALIASES.get(stripped)
    if alias:
        return alias

    parsed = urlparse(stripped)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return stripped


def _find_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None
