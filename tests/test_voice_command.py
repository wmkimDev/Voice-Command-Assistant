from __future__ import annotations

import unittest

from voice_command import extract_transcript_from_cli_output


class VoiceCommandTests(unittest.TestCase):
    def test_extract_transcript_from_text_output(self) -> None:
        self.assertEqual(extract_transcript_from_cli_output("새 탭 열어줘\n"), "새 탭 열어줘")

    def test_extract_transcript_from_json_text(self) -> None:
        self.assertEqual(extract_transcript_from_cli_output('{"text":"새 탭 열어줘"}'), "새 탭 열어줘")

    def test_extract_transcript_from_nested_json(self) -> None:
        self.assertEqual(
            extract_transcript_from_cli_output('{"data":{"transcript":"유튜브에서 고양이 검색해줘"}}'),
            "유튜브에서 고양이 검색해줘",
        )


if __name__ == "__main__":
    unittest.main()
