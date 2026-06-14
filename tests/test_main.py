from __future__ import annotations

import unittest

from main import describe_intent, describe_result


class MainOutputTests(unittest.TestCase):
    def test_describe_intent_focus_tab(self) -> None:
        self.assertEqual(
            describe_intent({"action": "focus_tab", "query": "ChatGPT", "url": None}),
            "Chrome 기존 탭 키워드 이동 실행 예정: ChatGPT",
        )

    def test_describe_intent_new_tab(self) -> None:
        self.assertEqual(
            describe_intent({"action": "new_tab", "query": None, "url": None}),
            "Chrome 빈 새 탭 열기 실행 예정",
        )

    def test_describe_result_success(self) -> None:
        self.assertEqual(
            describe_result({"ok": True, "action": "new_tab", "message": "new tab opened"}),
            "성공 (new_tab) - new tab opened",
        )

    def test_describe_result_youtube_search(self) -> None:
        self.assertEqual(
            describe_result(
                {
                    "ok": True,
                    "action": "youtube_search",
                    "message": "https://www.youtube.com/results?search_query=test",
                }
            ),
            "성공 (youtube_search) - https://www.youtube.com/results?search_query=test",
        )

    def test_describe_intent_youtube_new_tab(self) -> None:
        self.assertEqual(
            describe_intent({"action": "youtube_search_new_tab", "query": "lofi", "url": None}),
            "YouTube 검색 실행 예정(새 탭): lofi",
        )


if __name__ == "__main__":
    unittest.main()
