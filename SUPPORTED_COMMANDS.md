# Supported Commands

This document lists the command patterns currently handled by Voca's local rule parser.

Voca accepts Korean, English, and mixed-language transcripts, but the current command grammar is intentionally small and predictable. Use `--dry-run` when testing new phrasing.

```bash
python main.py --dry-run "유튜브에서 고양이 검색해줘"
```

## Text Input

Any transcript that does not match a known command is treated as dictated text.

| Transcript | Action |
|---|---|
| `안녕하세요 반갑습니다` | Paste text into the focused input |
| `hello how are you` | Paste text into the focused input |

Manual paste testing:

```bash
python main.py --delay 5 "이 문장이 입력되는지 테스트"
python main.py --delay 5 --keep-clipboard "이 문장이 입력되는지 테스트"
```

`--delay` gives you time to click the target input. `--keep-clipboard` keeps the text on the clipboard after the action so you can press `Cmd+V` manually for debugging.

## Chrome Tab Control

| Transcript pattern | Action |
|---|---|
| `새 탭 열어줘` | Open a blank Chrome tab |
| `새로운 탭 열어줘` | Open a blank Chrome tab |
| `{키워드} 탭으로 이동해줘` | Focus an existing tab whose title or URL contains the keyword |
| `{키워드} 탭 찾아줘` | Focus an existing tab whose title or URL contains the keyword |
| `{사이트별칭} 탭으로 이동해줘` | Focus the site if open, otherwise open it |
| `현재 탭에서 {사이트별칭}로 이동해줘` | Navigate the current Chrome tab to the site |

Tab keyword matching ignores spaces. For example, `베이직 기어` can match a tab titled `베이직기어`.

Known site aliases are defined in `config.py`.

Current aliases:

| Alias | URL |
|---|---|
| `쿠팡`, `coupang` | `https://www.coupang.com` |
| `유튜브`, `youtube` | `https://www.youtube.com` |
| `chatgpt`, `챗지피티` | `https://chatgpt.com` |
| `네이버`, `naver` | `https://www.naver.com` |
| `깃허브`, `github` | `https://github.com` |

## YouTube Search

| Transcript pattern | Action |
|---|---|
| `유튜브에서 {검색어} 검색해줘` | Search YouTube, reusing an existing YouTube tab if possible |
| `유튜브에 {검색어} 검색` | Search YouTube, reusing an existing YouTube tab if possible |
| `{검색어} 유튜브에 검색해줘` | Search YouTube, reusing an existing YouTube tab if possible |
| `유튜브에서 {검색어}라고 검색해줘` | Strip quote particle and search for `{검색어}` |
| `{검색어}이라 유튜브에서 검색해줘` | Strip quote particle and search for `{검색어}` |
| `새 탭에서 유튜브에 {검색어} 검색해줘` | Search YouTube in a new tab |
| `새 탭에서 {검색어}이라고 유튜브에 검색해줘` | Search YouTube in a new tab |
| `현재 탭에서 유튜브에 {검색어} 검색해줘` | Navigate the current Chrome tab to YouTube search |
| `현재 탭에서 {검색어}이라 유튜브에서 검색해줘` | Navigate the current Chrome tab to YouTube search |

Supported quote particles are stripped from the end of the extracted query:

- `이라고`
- `라고`
- `이라`
- `라`
- `으로`
- `로`
- `을`
- `를`

Examples:

```bash
python main.py --dry-run "유튜브에서 로파이 음악이라고 검색해줘"
python main.py --dry-run "로파이 음악이라 유튜브에서 검색해줘"
python main.py --dry-run "새 탭에서 로파이 음악이라고 유튜브에 검색해줘"
python main.py --dry-run "현재 탭에서 로파이 음악이라 유튜브에서 검색해줘"
```

## English Examples

| Transcript | Action |
|---|---|
| `search youtube for cat videos` | Search YouTube |
| `youtube jazz playlist` | Search YouTube |
| `open github` | Open or focus GitHub |
| `go to coupang` | Open or focus Coupang |
| `switch to docs tab` | Focus an existing tab matching `docs` |

## Unsupported or Risky Commands

Commands containing risky verbs are not executed directly by the local rule parser. They fall through to the Ollama fallback and usually become `unknown` unless an allowed intent is returned.

Examples of risky command words:

- `삭제`, `지워`
- `종료`, `꺼`
- `보내`, `전송`
- `실행`
- `delete`, `remove`, `quit`, `send`, `run`

## Output

Voca prints a short human-readable summary and then a JSON object.

Dry-run example:

```text
입력: 문서 탭으로 이동해줘
해석: Chrome 기존 탭 키워드 이동 실행 예정: 문서
{"ok": true, "dry_run": true, "intent": {"action": "focus_tab", "query": "문서", "url": null}}
```

Real-action example:

```text
입력: 새 탭 열어줘
해석: Chrome 빈 새 탭 열기 실행 예정
결과: 성공 (new_tab) - new tab opened
{"intent": {"action": "new_tab", "query": null, "url": null}, "result": {"ok": true, "action": "new_tab", "message": "new tab opened"}}
```

