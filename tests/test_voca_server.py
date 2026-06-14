from __future__ import annotations

import unittest

from voca_server import extract_transcript, process_transcript


class VocaServerTests(unittest.TestCase):
    def test_extract_plain_text(self) -> None:
        self.assertEqual(extract_transcript("현재 탭 닫아줘".encode()), "현재 탭 닫아줘")

    def test_extract_json_text(self) -> None:
        body = b'{"text": "\\uc720\\ud29c\\ube0c\\uc5d0\\uc11c \\uace0\\uc591\\uc774 \\uac80\\uc0c9\\ud574\\uc918"}'
        self.assertEqual(
            extract_transcript(body, "application/json"),
            "유튜브에서 고양이 검색해줘",
        )

    def test_extract_nested_json_transcript(self) -> None:
        body = '{"event": {"payload": {"transcript": "새 탭 열어줘"}}}'.encode()
        self.assertEqual(extract_transcript(body, "application/json"), "새 탭 열어줘")

    def test_extract_form_text(self) -> None:
        body = "%ED%98%84%EC%9E%AC+%ED%83%AD+%EB%8B%AB%EC%95%84%EC%A4%98=&text=%EC%83%88+%ED%83%AD+%EC%97%B4%EC%96%B4%EC%A4%98".encode()
        self.assertEqual(extract_transcript(body, "application/x-www-form-urlencoded"), "새 탭 열어줘")

    def test_extract_form_encoded_plain_text(self) -> None:
        body = "%EC%9C%A0%ED%8A%9C%EB%B8%8C%EC%97%90%EC%84%9C+%EB%A1%9C%ED%8C%8C%EC%9D%B4+%EC%9D%8C%EC%95%85+%EA%B2%80%EC%83%89%ED%95%B4%EC%A4%98".encode()
        self.assertEqual(
            extract_transcript(body, "application/x-www-form-urlencoded"),
            "유튜브에서 로파이 음악 검색해줘",
        )

    def test_dry_run_processes_transcript_without_action(self) -> None:
        response = process_transcript("새 탭 열어줘", dry_run=True, keep_clipboard=False)
        self.assertTrue(response["ok"])
        self.assertTrue(response["dry_run"])
        self.assertEqual(response["intent"]["action"], "new_tab")


if __name__ == "__main__":
    unittest.main()
