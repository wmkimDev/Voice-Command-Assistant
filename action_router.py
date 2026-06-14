from __future__ import annotations

import logging
from typing import Any, Callable

from actions.browser import close_current_tab, close_tab, focus_tab, navigate_current_tab, new_tab, open_tab
from actions.google import google_search, google_search_current_tab, google_search_new_tab
from actions.type_text import type_text
from actions.youtube import youtube_search, youtube_search_current_tab, youtube_search_new_tab

logger = logging.getLogger(__name__)

ActionResult = dict[str, Any]
Handler = Callable[[dict[str, Any]], ActionResult]


def _handle_type_text(intent: dict[str, Any]) -> ActionResult:
    return type_text(intent["query"], restore_clipboard=intent.get("restore_clipboard", True))


def _handle_youtube_search(intent: dict[str, Any]) -> ActionResult:
    return youtube_search(intent["query"])


def _handle_youtube_search_new_tab(intent: dict[str, Any]) -> ActionResult:
    return youtube_search_new_tab(intent["query"])


def _handle_youtube_search_current_tab(intent: dict[str, Any]) -> ActionResult:
    return youtube_search_current_tab(intent["query"])


def _handle_google_search(intent: dict[str, Any]) -> ActionResult:
    return google_search(intent["query"])


def _handle_google_search_new_tab(intent: dict[str, Any]) -> ActionResult:
    return google_search_new_tab(intent["query"])


def _handle_google_search_current_tab(intent: dict[str, Any]) -> ActionResult:
    return google_search_current_tab(intent["query"])


def _handle_open_tab(intent: dict[str, Any]) -> ActionResult:
    return open_tab(intent["url"])


def _handle_open_current_tab(intent: dict[str, Any]) -> ActionResult:
    return navigate_current_tab(intent["url"])


def _handle_new_tab(intent: dict[str, Any]) -> ActionResult:
    return new_tab()


def _handle_focus_tab(intent: dict[str, Any]) -> ActionResult:
    return focus_tab(intent["query"])


def _handle_close_current_tab(intent: dict[str, Any]) -> ActionResult:
    return close_current_tab()


def _handle_close_tab(intent: dict[str, Any]) -> ActionResult:
    return close_tab(intent["query"])


ACTION_HANDLERS: dict[str, Handler] = {
    "type_text": _handle_type_text,
    "youtube_search": _handle_youtube_search,
    "youtube_search_new_tab": _handle_youtube_search_new_tab,
    "youtube_search_current_tab": _handle_youtube_search_current_tab,
    "google_search": _handle_google_search,
    "google_search_new_tab": _handle_google_search_new_tab,
    "google_search_current_tab": _handle_google_search_current_tab,
    "open_tab": _handle_open_tab,
    "open_current_tab": _handle_open_current_tab,
    "new_tab": _handle_new_tab,
    "focus_tab": _handle_focus_tab,
    "close_current_tab": _handle_close_current_tab,
    "close_tab": _handle_close_tab,
}


def route_intent(intent: dict[str, Any]) -> ActionResult:
    action = intent.get("action")
    if action == "unknown":
        logger.info("Unknown intent: %s", intent)
        return {"ok": False, "action": "unknown", "message": "unknown intent"}

    handler = ACTION_HANDLERS.get(action)
    if handler is None:
        logger.warning("No handler for action: %s", action)
        return {"ok": False, "action": action, "message": "no handler"}

    try:
        return handler(intent)
    except KeyError as exc:
        logger.error("Missing required intent field for %s: %s", action, exc)
        return {"ok": False, "action": action, "message": f"missing field: {exc}"}
    except Exception as exc:
        logger.exception("Action failed: %s", action)
        return {"ok": False, "action": action, "message": str(exc)}
