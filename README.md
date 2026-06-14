# Voice Command Assistant

Voice Command Assistant, or **Voca**, is a local macOS voice-command automation prototype.

It takes a transcript from TypeWhisper, parses the intent with a fast local rule parser and an Ollama fallback, then controls Chrome or the currently focused input with Python and AppleScript.

## Features

- Type dictated text into the currently focused input.
- Open a blank Chrome tab.
- Focus an existing Chrome tab by title or URL keyword.
- Close the current tab or a tab matching a title/URL keyword.
- Open known sites such as YouTube, ChatGPT, Coupang, Naver, and GitHub.
- Search YouTube in one of three modes:
  - reuse an existing YouTube tab
  - open a new search tab
  - search in the current Chrome tab
- Search Google in the same tab modes.
- Preserve Korean, English, and mixed-language queries.
- Show a human-readable execution summary plus machine-readable JSON.
- Run fully locally after dependencies are installed.

## Requirements

- macOS
- Python 3.11+
- Google Chrome
- Ollama
- TypeWhisper, optional for CLI-only testing

Install the default Ollama model:

```bash
ollama pull qwen3:1.7b
```

macOS may ask for permissions when Voca controls Chrome or sends paste keystrokes:

- System Settings -> Privacy & Security -> Accessibility -> allow Terminal or your terminal app
- System Settings -> Privacy & Security -> Automation -> allow Terminal to control Google Chrome and System Events

## Setup

```bash
git clone git@github.com:wmkimDev/Voice-Command-Assistant.git
cd Voice-Command-Assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Dry Run

Dry-run mode parses the transcript but does not run AppleScript actions.

```bash
python main.py --dry-run "유튜브에서 고양이 검색해줘"
python main.py --dry-run "새 탭 열어줘"
python main.py --dry-run "문서 탭으로 이동해줘"
```

Output includes a human-readable summary first and a JSON object on the last line:

```text
입력: 문서 탭으로 이동해줘
해석: Chrome 기존 탭 키워드 이동 실행 예정: 문서
{"ok": true, "dry_run": true, "intent": {"action": "focus_tab", "query": "문서", "url": null}}
```

## Run

```bash
python main.py "새 탭 열어줘"
python main.py "문서 탭으로 이동해줘"
python main.py "유튜브에서 로파이 음악 검색해줘"
```

When running a real action, the output also includes a result line before the final JSON.

## Supported Commands

See [SUPPORTED_COMMANDS.md](SUPPORTED_COMMANDS.md) for the full list of currently supported command patterns.

Quick examples:

```bash
python main.py "쿠팡 탭으로 이동해줘"
python main.py "새 탭에서 유튜브에 로파이 음악 검색해줘"
python main.py "현재 탭에서 유튜브에 로파이 음악 검색해줘"
python main.py "로파이 음악이라고 유튜브에 검색해줘"
python main.py "구글에 서울 날씨 검색해줘"
```

## Text Input Testing

```bash
python main.py --delay 5 "이 문장이 입력되는지 테스트"
```

`--delay` gives you time to click the target input before Voca sends `Cmd+V`.

If the app reports success but the text does not appear, keep the clipboard for debugging:

```bash
python main.py --delay 5 --keep-clipboard "이 문장이 입력되는지 테스트"
```

After the command finishes, press `Cmd+V` manually in the target input.

- If manual paste works, the clipboard is correct and macOS is likely blocking the synthetic paste keystroke.
- If manual paste does not work, the target input was not focused or the clipboard was not set.

## TypeWhisper Integration

For Korean commands, use a cloud transcription engine such as OpenAI `gpt-4o-transcribe` or `gpt-4o-mini-transcribe`.

### Option A: Webhook Bridge

Start Voca's local webhook bridge:

```bash
python voca_server.py --dry-run
```

Use dry-run first. When parsing looks correct, restart without `--dry-run`:

```bash
python voca_server.py
```

In TypeWhisper:

1. Install the Webhook integration.
2. Set the webhook URL to `http://127.0.0.1:8765/typewhisper`.
3. Use `POST`.
4. Send the transcript as plain text, or as JSON with a `text` or `transcript` field.

The bridge accepts common payload shapes:

```json
{"text": "유튜브에서 로파이 음악 검색해줘"}
```

```json
{"transcript": "현재 탭 닫아줘"}
```

Plain text also works:

```text
새 탭 열어줘
```

You can verify the bridge manually:

```bash
curl -s http://127.0.0.1:8765/health
curl -s -X POST http://127.0.0.1:8765/typewhisper \
  -H 'Content-Type: application/json' \
  -d '{"text":"새 탭 열어줘"}'
```

### Option B: Script Integration

Configure TypeWhisper to run an external command after transcription. Prefer stdin so quotes and newlines survive:

```bash
printf '%s' "{transcript}" | python /path/to/Voice-Command-Assistant/main.py
```

Use dry-run first while tuning commands:

```bash
printf '%s' "{transcript}" | python /path/to/Voice-Command-Assistant/main.py --dry-run
```

This repo also includes wrapper scripts for TypeWhisper script integrations:

```bash
/path/to/Voice-Command-Assistant/scripts/voca_typewhisper_dry_run.sh
/path/to/Voice-Command-Assistant/scripts/voca_typewhisper.sh
/path/to/Voice-Command-Assistant/scripts/voca_typewhisper_silent.sh
```

If TypeWhisper's script integration treats stdout as replacement text, use
`voca_typewhisper_silent.sh`. It logs Voca output to `logs/typewhisper-script.log`
and returns empty stdout.

## Project Structure

```text
.
├── main.py
├── intent_parser.py
├── action_router.py
├── actions/
├── applescript/
├── tests/
├── config.py
└── REQUIREMENTS.md
```

## Tests

```bash
python -m unittest
```

AppleScript syntax can be checked with:

```bash
for f in applescript/*.applescript; do osacompile -o /tmp/voca-check.scpt "$f" || exit 1; done
```

## Notes

This is a personal local automation prototype, not a general-purpose voice assistant. The safest path is to keep frequent commands rule-based and use the Ollama fallback only for ambiguous intent parsing.
