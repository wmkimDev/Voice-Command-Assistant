from __future__ import annotations

import argparse
import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, unquote_plus, urlparse

from action_router import route_intent
from intent_parser import parse_intent
from logger import setup_logging

logger = logging.getLogger(__name__)

TEXT_KEYS = (
    "text",
    "transcript",
    "transcription",
    "final_text",
    "finalText",
    "processed_text",
    "processedText",
    "content",
    "message",
    "body",
    "result",
)


def extract_transcript(body: bytes, content_type: str = "") -> str:
    payload = body.decode("utf-8", errors="replace").strip()
    if not payload:
        return ""

    normalized_type = content_type.lower()
    if "application/x-www-form-urlencoded" in normalized_type:
        values = parse_qs(payload, keep_blank_values=True)
        for key in TEXT_KEYS:
            if key in values and values[key]:
                return values[key][0].strip()
        if "=" not in payload:
            return unquote_plus(payload).strip()
        return ""

    if "application/json" in normalized_type or payload.startswith(("{", "[")):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return payload

        if isinstance(data, str):
            return data.strip()

        value = find_text_value(data)
        return value.strip() if value else ""

    return payload


def find_text_value(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in TEXT_KEYS:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate
            if isinstance(candidate, (dict, list)):
                nested = find_text_value(candidate)
                if nested:
                    return nested

        for candidate in value.values():
            nested = find_text_value(candidate)
            if nested:
                return nested

    if isinstance(value, list):
        for item in value:
            nested = find_text_value(item)
            if nested:
                return nested

    return None


def process_transcript(transcript: str, *, dry_run: bool, keep_clipboard: bool) -> dict[str, Any]:
    intent = parse_intent(transcript)
    if dry_run:
        return {"ok": True, "dry_run": True, "transcript": transcript, "intent": intent}

    runtime_intent = intent.copy()
    if keep_clipboard and runtime_intent.get("action") == "type_text":
        runtime_intent["restore_clipboard"] = False

    result = route_intent(runtime_intent)
    return {"ok": bool(result.get("ok")), "dry_run": False, "transcript": transcript, "intent": intent, "result": result}


class VocaRequestHandler(BaseHTTPRequestHandler):
    dry_run = False
    keep_clipboard = False

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self.write_json(200, {"ok": True, "service": "voca"})
            return
        self.write_json(404, {"ok": False, "message": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in {"/", "/typewhisper", "/command"}:
            self.write_json(404, {"ok": False, "message": "not found"})
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length)
        transcript = extract_transcript(body, self.headers.get("Content-Type", ""))
        if not transcript:
            self.write_json(400, {"ok": False, "message": "empty transcript"})
            return

        logger.info("Received transcript: %s", transcript)
        response = process_transcript(
            transcript,
            dry_run=self.dry_run,
            keep_clipboard=self.keep_clipboard,
        )
        self.write_json(200 if response.get("ok") else 422, response)

    def write_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        logger.info("HTTP %s", format % args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local Voca HTTP bridge for TypeWhisper webhooks")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    parser.add_argument("--dry-run", action="store_true", help="Parse intent without running actions")
    parser.add_argument(
        "--keep-clipboard",
        action="store_true",
        help="Do not restore the previous clipboard after type_text.",
    )
    args = parser.parse_args(argv)

    setup_logging()
    VocaRequestHandler.dry_run = args.dry_run
    VocaRequestHandler.keep_clipboard = args.keep_clipboard

    server = ThreadingHTTPServer((args.host, args.port), VocaRequestHandler)
    logger.info("Voca server listening on http://%s:%s", args.host, args.port)
    print(f"Voca server listening on http://{args.host}:{args.port}/typewhisper")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Voca server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
