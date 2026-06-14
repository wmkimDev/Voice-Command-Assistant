from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "applescript"
OPEN_URL_SCRIPT = SCRIPT_DIR / "chrome_open_url.applescript"
NEW_TAB_SCRIPT = SCRIPT_DIR / "chrome_new_tab.applescript"
FOCUS_TAB_SCRIPT = SCRIPT_DIR / "chrome_focus_tab.applescript"
CLOSE_CURRENT_TAB_SCRIPT = SCRIPT_DIR / "chrome_close_current_tab.applescript"
CLOSE_TAB_SCRIPT = SCRIPT_DIR / "chrome_close_tab.applescript"


def open_tab(url: str) -> dict[str, object]:
    return _open_url(url, action="open_tab", mode="focus")


def navigate_url(url: str, action: str = "navigate_url") -> dict[str, object]:
    return _open_url(url, action=action, mode="navigate")


def open_new_url(url: str, action: str = "open_new_url") -> dict[str, object]:
    return _open_url(url, action=action, mode="new")


def navigate_current_tab(url: str, action: str = "open_current_tab") -> dict[str, object]:
    return _open_url(url, action=action, mode="current")


def _open_url(url: str, action: str, mode: str) -> dict[str, object]:
    if not _is_safe_url(url):
        logger.warning("Blocked invalid URL: %s", url)
        return {"ok": False, "action": action, "message": "invalid url"}

    host = urlparse(url).netloc
    try:
        subprocess.run(
            ["osascript", str(OPEN_URL_SCRIPT), url, host, mode],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to open Chrome URL: %s", exc.stderr.strip())
        return {"ok": False, "action": action, "message": exc.stderr.strip() or str(exc)}

    return {"ok": True, "action": action, "message": url}


def new_tab() -> dict[str, object]:
    try:
        subprocess.run(
            ["osascript", str(NEW_TAB_SCRIPT)],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to create Chrome tab: %s", exc.stderr.strip())
        return {"ok": False, "action": "new_tab", "message": exc.stderr.strip() or str(exc)}

    return {"ok": True, "action": "new_tab", "message": "new tab opened"}


def focus_tab(keyword: str) -> dict[str, object]:
    cleaned = keyword.strip()
    if not cleaned:
        return {"ok": False, "action": "focus_tab", "message": "empty keyword"}

    try:
        result = subprocess.run(
            ["osascript", str(FOCUS_TAB_SCRIPT), cleaned],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to focus Chrome tab: %s", exc.stderr.strip())
        return {"ok": False, "action": "focus_tab", "message": exc.stderr.strip() or str(exc)}

    output = result.stdout.strip()
    if output == "found":
        return {"ok": True, "action": "focus_tab", "message": cleaned}
    return {"ok": False, "action": "focus_tab", "message": f"tab not found: {cleaned}"}


def close_current_tab() -> dict[str, object]:
    try:
        result = subprocess.run(
            ["osascript", str(CLOSE_CURRENT_TAB_SCRIPT)],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to close current Chrome tab: %s", exc.stderr.strip())
        return {"ok": False, "action": "close_current_tab", "message": exc.stderr.strip() or str(exc)}

    message = result.stdout.strip() or "current tab closed"
    return {"ok": True, "action": "close_current_tab", "message": message}


def close_tab(keyword: str) -> dict[str, object]:
    cleaned = keyword.strip()
    if not cleaned:
        return {"ok": False, "action": "close_tab", "message": "empty keyword"}

    try:
        result = subprocess.run(
            ["osascript", str(CLOSE_TAB_SCRIPT), cleaned],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to close Chrome tab: %s", exc.stderr.strip())
        return {"ok": False, "action": "close_tab", "message": exc.stderr.strip() or str(exc)}

    output = result.stdout.strip()
    if output.startswith("closed:"):
        return {"ok": True, "action": "close_tab", "message": output.removeprefix("closed:").strip()}
    return {"ok": False, "action": "close_tab", "message": f"tab not found: {cleaned}"}


def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
