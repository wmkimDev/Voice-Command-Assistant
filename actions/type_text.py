from __future__ import annotations

import logging
import subprocess
import time

logger = logging.getLogger(__name__)

PASTE_SETTLE_SECONDS = 1.5


def type_text(text: str, restore_clipboard: bool = True) -> dict[str, object]:
    previous = _get_clipboard() if restore_clipboard else None
    try:
        target_app = _frontmost_app()
        _set_clipboard(text)
        current = _get_clipboard()
        if current != text:
            return {"ok": False, "action": "type_text", "message": "failed to set clipboard"}
        _paste_clipboard()
        time.sleep(PASTE_SETTLE_SECONDS)
        restore_note = "clipboard restored" if restore_clipboard else "clipboard kept"
        return {"ok": True, "action": "type_text", "message": f"text pasted to {target_app}; {restore_note}"}
    except subprocess.SubprocessError as exc:
        logger.error("Failed to paste text: %s", exc)
        return {"ok": False, "action": "type_text", "message": str(exc)}
    finally:
        if restore_clipboard and previous is not None:
            try:
                _set_clipboard(previous)
            except subprocess.SubprocessError as exc:
                logger.warning("Failed to restore clipboard: %s", exc)


def _get_clipboard() -> str:
    result = subprocess.run(["pbpaste"], text=True, capture_output=True, check=True)
    return result.stdout


def _set_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=True)


def _paste_clipboard() -> None:
    script = 'tell application "System Events" to key code 9 using command down'
    subprocess.run(["osascript", "-e", script], text=True, capture_output=True, check=True)


def _frontmost_app() -> str:
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    result = subprocess.run(["osascript", "-e", script], text=True, capture_output=True, check=True)
    return result.stdout.strip() or "unknown app"
