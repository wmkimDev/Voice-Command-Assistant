# Voice Command Assistant — Requirements

## 프로젝트 개요

맥북에서 음성 명령으로 브라우저 및 시스템을 제어하는 로컬 어시스턴트.
TypeWhisper(STT) + Ollama(인텐트 파싱) + AppleScript/Python(액션 실행) 구성.
인터넷 불필요, 완전 로컬 실행.

---

## 기술 스택

| 구성요소 | 도구 | 비고 |
|---|---|---|
| STT | TypeWhisper | 로컬 Whisper 기반, 글로벌 핫키 지원 |
| 인텐트 파싱 | Ollama + qwen3:1.7b | 로컬 LLM, JSON 출력 |
| 액션 실행 | Python + AppleScript | 크롬 제어, 텍스트 입력 |
| 진입점 | TypeWhisper webhook 또는 CLI | STT 결과를 Python으로 전달 |

### 환경
- macOS (Apple Silicon, M4 Pro 기준)
- Python 3.11+
- Ollama 설치 및 `qwen3:1.7b` 모델 pull 완료
- TypeWhisper 설치 완료
- Google Chrome 사용

### macOS 권한
AppleScript와 클립보드 기반 입력을 사용하므로 최초 실행 시 아래 권한 설정이 필요할 수 있다.

- Accessibility: Python/Terminal 또는 패키징된 앱이 키 입력과 앱 포커스를 제어
- Automation: Python/Terminal 또는 앱이 Google Chrome, System Events 제어
- Input Monitoring: 환경에 따라 전역 핫키 또는 키 입력 자동화에 필요

권한이 없으면 액션 실행은 실패하되, 프로그램은 예외로 종료하지 않고 원인을 로그로 남겨야 한다.

---

## 아키텍처

```
[핫키 or 웨이크워드]
        ↓
[TypeWhisper] — 음성 → 텍스트
        ↓
[Python: main.py]
        ↓
[Ollama: qwen3:1.7b] — 텍스트 → Intent JSON
        ↓
[Action Router] — JSON → 액션 함수 호출
        ↓
[AppleScript / subprocess] — 실제 실행
```

---

## Intent JSON 스펙

LLM은 항상 아래 형식의 JSON만 출력해야 한다. 다른 텍스트 없이 순수 JSON만.

```json
{
  "action": "<action_name>",
  "query": "<검색어 또는 입력 텍스트, 해당 없으면 null>",
  "url": "<이동할 URL, 해당 없으면 null>"
}
```

### action 종류 (MVP)

| action | 설명 | 필요 필드 |
|---|---|---|
| `type_text` | 현재 포커스된 입력창에 텍스트 입력 | `query` |
| `youtube_search` | 크롬에서 유튜브 검색 | `query` |
| `youtube_search_new_tab` | 새 탭에서 유튜브 검색 | `query` |
| `youtube_search_current_tab` | 현재 Chrome 탭에서 유튜브 검색 | `query` |
| `google_search` | 크롬에서 구글 검색 | `query` |
| `google_search_new_tab` | 새 탭에서 구글 검색 | `query` |
| `google_search_current_tab` | 현재 Chrome 탭에서 구글 검색 | `query` |
| `chatgpt_ask` | ChatGPT 탭 찾아서 입력창에 텍스트 입력 | `query` |
| `open_tab` | 특정 URL 또는 URL 별칭으로 이동. 이미 열려 있으면 포커스, 없으면 새 탭으로 열기 | `url` |
| `open_current_tab` | 현재 Chrome 탭을 특정 URL 또는 URL 별칭으로 이동 | `url` |
| `new_tab` | 크롬에 빈 새 탭 열기 | — |
| `focus_tab` | 기존 크롬 탭을 제목 또는 URL 키워드로 찾아 포커스 | `query` |
| `unknown` | 파싱 실패 또는 해당 없음 | — |

### 검증 규칙

- `action`은 위 목록 중 하나만 허용
- 필수 필드가 비어 있으면 `unknown` 처리
- `query`는 입력 언어를 보존하고 번역하지 않음
- `url`은 `http://` 또는 `https://`만 허용
- URL 별칭은 `config.py`의 `URL_ALIASES`를 우선 사용
- LLM이 알 수 없는 사이트나 위험한 URL을 생성하면 실행하지 않고 `unknown` 처리

### 예시 — 한국어

입력: "유튜브에서 고양이 검색해줘"
```json
{"action": "youtube_search", "query": "고양이", "url": null}
```

입력: "ChatGPT에 파이썬 정렬 알고리즘 물어봐줘"
```json
{"action": "chatgpt_ask", "query": "파이썬 정렬 알고리즘", "url": null}
```

입력: "쿠팡 탭으로 이동해줘"
```json
{"action": "open_tab", "query": null, "url": "https://www.coupang.com"}
```

입력: "안녕하세요 반갑습니다" (딕테이션 모드)
```json
{"action": "type_text", "query": "안녕하세요 반갑습니다", "url": null}
```

### 예시 — 영어

입력: "search YouTube for cat videos"
```json
{"action": "youtube_search", "query": "cat videos", "url": null}
```

입력: "ask ChatGPT about sorting algorithms in Python"
```json
{"action": "chatgpt_ask", "query": "sorting algorithms in Python", "url": null}
```

입력: "go to Coupang"
```json
{"action": "open_tab", "query": null, "url": "https://www.coupang.com"}
```

입력: "hello how are you" (dictation mode)
```json
{"action": "type_text", "query": "hello how are you", "url": null}
```

### 예시 — 한영 혼용 (코드스위칭)

입력: "유튜브에서 cat videos 검색해줘"
```json
{"action": "youtube_search", "query": "cat videos", "url": null}
```

입력: "ChatGPT한테 Python list comprehension 물어봐줘"
```json
{"action": "chatgpt_ask", "query": "Python list comprehension", "url": null}
```

---

## 파일 구조

```
voice-assistant/
├── main.py              # 진입점, STT 결과 수신 및 파이프라인 실행
├── intent_parser.py     # Ollama 호출, JSON 파싱
├── action_router.py     # action별 함수 라우팅
├── actions/
│   ├── __init__.py
│   ├── type_text.py     # 현재 입력창에 텍스트 입력
│   ├── youtube.py       # 유튜브 검색
│   ├── chatgpt.py       # ChatGPT 탭 찾아서 입력
│   └── browser.py       # 크롬 탭 이동/열기 (open_tab)
├── applescript/
│   ├── type_text.applescript
│   ├── chrome_search.applescript
│   ├── chrome_find_tab.applescript
│   ├── chrome_focus_tab.applescript
│   ├── chrome_new_tab.applescript
│   └── chrome_open_url.applescript
├── config.py            # 설정값 (모델명, URL 별칭 등)
├── requirements.txt
├── tests/
│   ├── test_intent_parser.py
│   └── test_action_router.py
├── logs/
│   └── voca.log
└── README.md
```

---

## 각 모듈 상세 요구사항

### main.py
- TypeWhisper로부터 텍스트를 stdin 또는 CLI 인자로 수신
- 우선순위: CLI 인자 → stdin → 클립보드 fallback
- transcript 안의 따옴표, 줄바꿈, 특수문자 보존
- `intent_parser.py` 호출하여 JSON 획득
- `action_router.py`에 JSON 전달
- 실행 결과 로깅 (stdout)
- `--dry-run` 옵션 지원: intent JSON만 출력하고 액션 실행하지 않음

### intent_parser.py
- Ollama REST API (`http://localhost:11434/api/generate`) 호출
- 모델: `qwen3:1.7b`
- Ollama 요청은 `stream: false`, 가능하면 `format: "json"` 사용
- 시스템 프롬프트에 action 목록과 JSON 스펙 명시
- **다국어 처리**: 시스템 프롬프트에 한국어/영어/한영혼용 예시를 모두 포함할 것
  - 어떤 언어로 입력이 들어와도 항상 JSON만 출력하도록 명시
  - `query` 필드는 입력 언어 그대로 보존 (번역하지 않음)
- 응답에서 JSON만 추출 (`json.loads` 우선, 실패 시 JSON object 부분만 추출)
- 모델 응답에 `<think>...</think>` 또는 설명 문장이 섞이면 제거 후 파싱
- 파싱 실패 시 `{"action": "unknown", "query": null, "url": null}` 반환
- 일반 파싱 타임아웃: 5초
- 앱 시작 시 워밍업 타임아웃: 30초

#### 시스템 프롬프트 작성 가이드
```
You are a voice command parser. The user speaks in Korean, English, or a mix of both.
Your job is to parse the user's intent and output ONLY a JSON object. No explanation, no other text.

Available actions: type_text, youtube_search, chatgpt_ask, open_tab, new_tab, focus_tab, unknown
...
(한국어/영어/혼용 예시 각각 포함할 것)
```

### action_router.py
- action 이름 → 함수 매핑 딕셔너리
- unknown 액션은 로그만 남기고 종료
- 새 액션 추가 시 딕셔너리에 항목 하나만 추가하면 되도록 설계

### actions/type_text.py
- AppleScript `keystroke` 또는 `set the clipboard` + Cmd+V 방식으로 텍스트 입력
- 한국어 포함 유니코드 처리 필수 (keystroke는 한국어 안 됨 → 클립보드 방식 사용)
- 입력 전 기존 클립보드 내용을 저장하고, 붙여넣기 후 가능한 경우 복원
- 붙여넣기 실패 시 기존 클립보드를 복원하고 오류 로그 출력

### actions/youtube.py
- 크롬에서 열린 유튜브 탭이 있으면 그 탭으로 이동 후 검색
- 없으면 새 탭으로 `https://www.youtube.com/results?search_query={query}` 열기
- `query`는 URL 인코딩 필수

### actions/chatgpt.py
- 크롬에서 `chatgpt.com` 포함된 탭 찾기
- 탭 없으면 새 탭으로 `https://chatgpt.com` 열기
- 입력창 포커스 후 텍스트 입력 (클립보드 방식)
- 자동 전송은 하지 않음 (사용자가 Enter 직접)
- 입력창 포커싱 실패 시 탭만 열고 오류 로그 출력

### actions/browser.py
- `open_tab` 액션 처리
- `url` 필드의 URL로 크롬 탭 이동
- 해당 URL이 이미 열려있으면 그 탭으로 포커스, 없으면 새 탭
- URL 검증 후 실행 (`http://`, `https://`만 허용)
- `new_tab` 액션 처리: 빈 새 탭 생성
- `focus_tab` 액션 처리: `query` 키워드가 제목 또는 URL에 포함된 기존 탭으로 포커스
- `focus_tab`은 탭을 찾지 못하면 새 탭을 만들지 않고 실패 결과 반환

### config.py
- Ollama 엔드포인트, 모델명
- URL 별칭 딕셔너리 (예: "쿠팡" → "https://www.coupang.com")
- 별칭은 LLM 시스템 프롬프트에도 주입하여 파싱 정확도 향상

---

## 메뉴바 앱

voca는 최종적으로 메뉴바 앱으로 동작한다. 부팅 시 자동 시작하지 않으며, 사용자가 직접 실행한다.

메뉴바 앱은 1차 MVP 이후 1.5차 범위로 구현한다. 1차 MVP에서는 CLI 실행과 TypeWhisper 외부 커맨드 연동을 먼저 완성한다.

### 동작 방식
- 메뉴바 아이콘 클릭 → Start / Stop 토글
- **Start 시**:
  1. Ollama 서버 실행 확인 (미실행 시 자동 시작)
  2. 더미 쿼리로 `qwen3:1.7b` 워밍업 (콜드 스타트 제거)
  3. TypeWhisper 핫키 활성화
  4. 메뉴바 아이콘 활성 상태로 변경
- **Stop 시**:
  1. 핫키 비활성화
  2. 리소스 정리
  3. 메뉴바 아이콘 비활성 상태로 변경

### 구현
- Python `rumps` 라이브러리로 메뉴바 앱 구현
- 메뉴 항목: Start/Stop, 구분선, Quit

### 성능 최적화
- Ollama는 한번 워밍업되면 이후 응답 거의 즉각
- Ollama `generate` API 스트리밍 비활성화 (짧은 JSON 출력엔 단발이 더 빠름)
- TypeWhisper STT는 Metal 가속으로 M4 Pro에서 빠르게 동작

---

## 로깅 및 오류 처리

- stdout에는 사용자에게 필요한 실행 결과를 간단히 출력
- 상세 로그는 `logs/voca.log`에 기록
- Ollama 미실행, 모델 없음, Chrome 미실행, AppleScript 권한 없음, URL 검증 실패를 구분해서 로그 출력
- 액션 실패 시 프로그램 전체가 크래시되지 않고 실패 결과를 반환
- `--dry-run`에서는 Ollama intent 결과와 검증 결과만 출력하고 AppleScript는 실행하지 않음

---

## 테스트 기준

- `intent_parser.py`는 한국어/영어/한영혼용 예시를 단위 테스트로 검증
- malformed JSON, `<think>` 포함 응답, 빈 응답은 `unknown`으로 fallback
- `action_router.py`는 알 수 없는 action, 필수 필드 누락, 정상 라우팅을 테스트
- AppleScript가 필요한 액션은 dry-run 또는 mock 기반 테스트 우선

---

## TypeWhisper 연동 방식

MVP에서는 TypeWhisper 전사 완료 후 외부 커맨드를 실행하는 방식을 우선 사용한다.
Automation API, Watch Folder, 클립보드 감시는 MVP 이후 확장으로 둔다.

권장 방식: TypeWhisper에서 전사 완료 후 transcript를 stdin으로 전달
```
printf '%s' "{transcript}" | python /path/to/voice-assistant/main.py
```

CLI 인자로 넘기는 방식도 지원하되, transcript 안의 따옴표, 줄바꿈, 특수문자가 깨질 수 있으므로 stdin 방식을 기본값으로 문서화한다.

---

## 확장 가이드

새 액션 추가 방법:

1. `actions/` 에 새 파일 추가 (예: `google_search.py`)
2. `action_router.py` 딕셔너리에 항목 추가
3. `config.py`의 시스템 프롬프트에 새 action 설명 추가
4. 끝

---

## 1차 MVP 범위

- [ ] `type_text` 액션 (한국어 클립보드 방식)
- [ ] `youtube_search` 액션
- [ ] `open_tab` 액션
- [ ] `new_tab` 액션
- [ ] `focus_tab` 액션
- [ ] Ollama intent_parser (qwen3:1.7b)
- [ ] TypeWhisper 외부 커맨드 연동 (stdin 기본)
- [ ] config.py URL 별칭
- [ ] `--dry-run` 모드
- [ ] 기본 로그 파일
- [ ] intent_parser/action_router 단위 테스트

## 1.5차 확장

- [ ] `chatgpt_ask` 액션
- [ ] 메뉴바 앱 (`rumps`)
- [ ] Ollama 서버 실행 확인 및 워밍업
- [ ] Start/Stop 토글

## 2차 확장 (MVP 이후)

- [ ] 웨이크워드 트리거 (핫키 대신)
- [ ] `google_search` 액션
- [ ] 더 많은 URL 별칭 (네이버, 쿠팡, 깃헙 등)
- [ ] 실행 결과 음성 피드백 (TTS)
- [ ] 오류 시 알림 (macOS notification)
