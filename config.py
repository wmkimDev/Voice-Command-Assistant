OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:1.7b"

PARSE_TIMEOUT_SECONDS = 5
WARMUP_TIMEOUT_SECONDS = 30

LOG_FILE = "logs/voca.log"

ALLOWED_ACTIONS = {
    "type_text",
    "youtube_search",
    "youtube_search_new_tab",
    "youtube_search_current_tab",
    "google_search",
    "google_search_new_tab",
    "google_search_current_tab",
    "chatgpt_ask",
    "open_tab",
    "open_current_tab",
    "new_tab",
    "focus_tab",
    "close_current_tab",
    "close_tab",
    "unknown",
}

URL_ALIASES = {
    "쿠팡": "https://www.coupang.com",
    "coupang": "https://www.coupang.com",
    "유튜브": "https://www.youtube.com",
    "youtube": "https://www.youtube.com",
    "구글": "https://www.google.com",
    "google": "https://www.google.com",
    "chatgpt": "https://chatgpt.com",
    "챗지피티": "https://chatgpt.com",
    "네이버": "https://www.naver.com",
    "naver": "https://www.naver.com",
    "깃허브": "https://github.com",
    "github": "https://github.com",
}
