from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import action_router
from action_router import route_intent


class ActionRouterTests(unittest.TestCase):
    def test_unknown_intent_returns_failure(self) -> None:
        result = route_intent({"action": "unknown", "query": None, "url": None})
        self.assertFalse(result["ok"])
        self.assertEqual(result["action"], "unknown")

    def test_missing_handler_returns_failure(self) -> None:
        with patch.object(action_router.logger, "warning"):
            result = route_intent({"action": "chatgpt_ask", "query": "hello", "url": None})

        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "no handler")

    def test_new_tab_handler_exists(self) -> None:
        self.assertIn("new_tab", action_router.ACTION_HANDLERS)

    def test_focus_tab_handler_exists(self) -> None:
        self.assertIn("focus_tab", action_router.ACTION_HANDLERS)

    def test_youtube_mode_handlers_exist(self) -> None:
        self.assertIn("youtube_search_new_tab", action_router.ACTION_HANDLERS)
        self.assertIn("youtube_search_current_tab", action_router.ACTION_HANDLERS)

    def test_current_tab_handler_exists(self) -> None:
        self.assertIn("open_current_tab", action_router.ACTION_HANDLERS)

    def test_routes_known_action(self) -> None:
        handler = Mock(return_value={"ok": True, "action": "fake", "message": "done"})
        with patch.dict(action_router.ACTION_HANDLERS, {"fake": handler}):
            result = route_intent({"action": "fake", "query": "hello", "url": None})

        self.assertTrue(result["ok"])
        handler.assert_called_once_with({"action": "fake", "query": "hello", "url": None})


if __name__ == "__main__":
    unittest.main()
