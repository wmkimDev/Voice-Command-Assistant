from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from intent_parser import (
    UNKNOWN_INTENT,
    extract_json_object,
    parse_intent,
    parse_local_intent,
    validate_intent,
)


class IntentParserTests(unittest.TestCase):
    def test_extract_json_object_from_clean_json(self) -> None:
        raw = '{"action":"youtube_search","query":"고양이","url":null}'
        self.assertEqual(
            extract_json_object(raw),
            {"action": "youtube_search", "query": "고양이", "url": None},
        )

    def test_extract_json_object_removes_thinking_text(self) -> None:
        raw = '<think>reasoning</think>\n{"action":"type_text","query":"hello","url":null}'
        self.assertEqual(
            extract_json_object(raw),
            {"action": "type_text", "query": "hello", "url": None},
        )

    def test_extract_json_object_from_extra_text(self) -> None:
        raw = 'Here is JSON: {"action":"open_tab","query":null,"url":"https://github.com"} done'
        self.assertEqual(
            extract_json_object(raw),
            {"action": "open_tab", "query": None, "url": "https://github.com"},
        )

    def test_validate_rejects_unknown_action(self) -> None:
        self.assertEqual(
            validate_intent({"action": "delete_files", "query": None, "url": None}),
            UNKNOWN_INTENT,
        )

    def test_validate_requires_query_for_text_actions(self) -> None:
        self.assertEqual(
            validate_intent({"action": "youtube_search", "query": "", "url": None}),
            UNKNOWN_INTENT,
        )

    def test_validate_open_tab_accepts_safe_url(self) -> None:
        self.assertEqual(
            validate_intent({"action": "open_tab", "query": None, "url": "https://www.coupang.com"}),
            {"action": "open_tab", "query": None, "url": "https://www.coupang.com"},
        )

    def test_validate_open_tab_rejects_unsafe_url(self) -> None:
        self.assertEqual(
            validate_intent({"action": "open_tab", "query": None, "url": "file:///tmp/a"}),
            UNKNOWN_INTENT,
        )

    def test_local_parser_handles_korean_youtube_search(self) -> None:
        self.assertEqual(
            parse_local_intent("유튜브에서 고양이 검색해줘"),
            {"action": "youtube_search", "query": "고양이", "url": None},
        )

    def test_local_parser_strips_quoted_search_particle_after_query(self) -> None:
        self.assertEqual(
            parse_local_intent("유튜브에서 로파이 음악이라고 검색해줘"),
            {"action": "youtube_search", "query": "로파이 음악", "url": None},
        )
        self.assertEqual(
            parse_local_intent("유튜브에서 로파이 음악이라 검색해줘"),
            {"action": "youtube_search", "query": "로파이 음악", "url": None},
        )

    def test_local_parser_handles_query_before_youtube(self) -> None:
        self.assertEqual(
            parse_local_intent("로파이 음악이라고 유튜브에 검색해줘"),
            {"action": "youtube_search", "query": "로파이 음악", "url": None},
        )
        self.assertEqual(
            parse_local_intent("로파이 음악이라 유튜브에서 검색해줘"),
            {"action": "youtube_search", "query": "로파이 음악", "url": None},
        )

    def test_local_parser_handles_youtube_search_in_new_tab(self) -> None:
        self.assertEqual(
            parse_local_intent("새 탭에서 유튜브에 로파이 음악 검색해줘"),
            {"action": "youtube_search_new_tab", "query": "로파이 음악", "url": None},
        )
        self.assertEqual(
            parse_local_intent("새 탭에서 로파이 음악이라고 유튜브에 검색해줘"),
            {"action": "youtube_search_new_tab", "query": "로파이 음악", "url": None},
        )

    def test_local_parser_handles_youtube_search_in_current_tab(self) -> None:
        self.assertEqual(
            parse_local_intent("현재 탭에서 유튜브에 로파이 음악 검색해줘"),
            {"action": "youtube_search_current_tab", "query": "로파이 음악", "url": None},
        )
        self.assertEqual(
            parse_local_intent("현재 탭에서 로파이 음악이라 유튜브에서 검색해줘"),
            {"action": "youtube_search_current_tab", "query": "로파이 음악", "url": None},
        )

    def test_local_parser_handles_current_tab_site_navigation(self) -> None:
        self.assertEqual(
            parse_local_intent("현재 탭에서 유튜브로 이동해줘"),
            {"action": "open_current_tab", "query": None, "url": "https://www.youtube.com"},
        )

    def test_local_parser_handles_url_alias(self) -> None:
        self.assertEqual(
            parse_local_intent("쿠팡 탭으로 이동해줘"),
            {"action": "open_tab", "query": None, "url": "https://www.coupang.com"},
        )

    def test_local_parser_handles_new_tab(self) -> None:
        self.assertEqual(
            parse_local_intent("새 탭 열어줘"),
            {"action": "new_tab", "query": None, "url": None},
        )

    def test_local_parser_handles_focus_tab_by_keyword(self) -> None:
        self.assertEqual(
            parse_local_intent("문서 탭으로 이동해줘"),
            {"action": "focus_tab", "query": "문서", "url": None},
        )

    def test_local_parser_handles_english_focus_tab_by_keyword(self) -> None:
        self.assertEqual(
            parse_local_intent("switch to docs tab"),
            {"action": "focus_tab", "query": "docs", "url": None},
        )

    def test_local_parser_uses_type_text_for_dictation(self) -> None:
        self.assertEqual(
            parse_local_intent("안녕하세요 반갑습니다"),
            {"action": "type_text", "query": "안녕하세요 반갑습니다", "url": None},
        )

    @patch("intent_parser.requests.post")
    def test_parse_intent_uses_ollama_response(self, post: Mock) -> None:
        response = Mock()
        response.json.return_value = {
            "response": '{"action":"youtube_search","query":"cat videos","url":null}'
        }
        response.raise_for_status.return_value = None
        post.return_value = response

        self.assertEqual(
            parse_intent("run custom command"),
            {"action": "youtube_search", "query": "cat videos", "url": None},
        )


if __name__ == "__main__":
    unittest.main()
