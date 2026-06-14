from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from typing import Any

from action_router import route_intent
from intent_parser import parse_intent
from logger import setup_logging

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local voice command assistant")
    parser.add_argument("transcript", nargs="*", help="Transcript text from TypeWhisper")
    parser.add_argument("--dry-run", action="store_true", help="Parse intent without running actions")
    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Wait before running the action. Useful when manually testing paste into another app.",
    )
    parser.add_argument(
        "--keep-clipboard",
        action="store_true",
        help="Do not restore the previous clipboard after type_text. Useful for paste debugging.",
    )
    args = parser.parse_args(argv)

    setup_logging()

    transcript = read_transcript(args.transcript)
    if not transcript.strip():
        print(json.dumps({"ok": False, "message": "empty transcript"}, ensure_ascii=False))
        return 1

    intent = parse_intent(transcript)
    print(f"입력: {transcript}")
    print(f"해석: {describe_intent(intent)}")
    logger.info("Parsed intent: %s", intent)

    if args.dry_run:
        print(json.dumps({"ok": True, "dry_run": True, "intent": intent}, ensure_ascii=False))
        return 0

    if args.delay > 0:
        print(f"대기: {args.delay:g}초 안에 대상 입력창을 클릭하세요.")
        time.sleep(args.delay)

    runtime_intent = intent.copy()
    if args.keep_clipboard and runtime_intent.get("action") == "type_text":
        runtime_intent["restore_clipboard"] = False

    result = route_intent(runtime_intent)
    print(f"결과: {describe_result(result)}")
    logger.info("Action result: %s", result)
    print(json.dumps({"intent": intent, "result": result}, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def read_transcript(cli_parts: list[str]) -> str:
    if cli_parts:
        return " ".join(cli_parts)

    if not sys.stdin.isatty():
        value = sys.stdin.read()
        if value.strip():
            return value

    try:
        result = subprocess.run(["pbpaste"], text=True, capture_output=True, check=True)
        return result.stdout
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error("Failed to read clipboard fallback: %s", exc)
        return ""


def describe_intent(intent: dict[str, Any]) -> str:
    action = intent.get("action")
    query = intent.get("query")
    url = intent.get("url")

    if action == "youtube_search":
        return f"YouTube 검색 실행 예정(기존 YouTube 탭 재사용): {query}"
    if action == "youtube_search_new_tab":
        return f"YouTube 검색 실행 예정(새 탭): {query}"
    if action == "youtube_search_current_tab":
        return f"YouTube 검색 실행 예정(현재 탭): {query}"
    if action == "google_search":
        return f"Google 검색 실행 예정(기존 Google 탭 재사용): {query}"
    if action == "google_search_new_tab":
        return f"Google 검색 실행 예정(새 탭): {query}"
    if action == "google_search_current_tab":
        return f"Google 검색 실행 예정(현재 탭): {query}"
    if action == "open_tab":
        return f"Chrome URL/사이트 이동 실행 예정: {url}"
    if action == "open_current_tab":
        return f"현재 Chrome 탭에서 URL/사이트 이동 실행 예정: {url}"
    if action == "new_tab":
        return "Chrome 빈 새 탭 열기 실행 예정"
    if action == "focus_tab":
        return f"Chrome 기존 탭 키워드 이동 실행 예정: {query}"
    if action == "type_text":
        return f"현재 입력창에 텍스트 입력 예정: {query}"
    if action == "chatgpt_ask":
        return f"ChatGPT 입력 예정: {query}"
    return "알 수 없는 명령이라 실행하지 않음"


def describe_result(result: dict[str, Any]) -> str:
    status = "성공" if result.get("ok") else "실패"
    action = result.get("action", "unknown")
    message = result.get("message", "")
    if message:
        return f"{status} ({action}) - {message}"
    return f"{status} ({action})"


if __name__ == "__main__":
    raise SystemExit(main())
