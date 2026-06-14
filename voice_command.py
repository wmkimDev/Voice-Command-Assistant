from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

from action_router import route_intent
from intent_parser import parse_intent
from logger import setup_logging
from main import describe_intent, describe_result

logger = logging.getLogger(__name__)

DEFAULT_TYPEWHISPER_CLI = "/Applications/TypeWhisper.app/Contents/MacOS/typewhisper-cli"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record a voice command and run it through TypeWhisper")
    parser.add_argument("--duration", type=float, default=3.0, help="Recording duration in seconds")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Recording sample rate")
    parser.add_argument("--channels", type=int, default=1, help="Recording channel count")
    parser.add_argument("--dry-run", action="store_true", help="Transcribe and parse without running actions")
    parser.add_argument("--loop", action="store_true", help="Keep listening until Ctrl+C")
    parser.add_argument("--keep-audio", action="store_true", help="Keep recorded wav files in logs/audio")
    parser.add_argument(
        "--allow-text",
        action="store_true",
        help="Allow plain dictation text to be pasted. By default voice mode runs commands only.",
    )
    parser.add_argument("--language", help="TypeWhisper source language override, e.g. ko or en")
    parser.add_argument(
        "--language-hint",
        action="append",
        default=[],
        help="TypeWhisper language hint. Can be repeated.",
    )
    parser.add_argument("--engine", help="TypeWhisper engine override")
    parser.add_argument("--model", help="TypeWhisper model override")
    parser.add_argument("--port", type=int, help="TypeWhisper API server port")
    parser.add_argument("--api-token", help="TypeWhisper API bearer token")
    parser.add_argument("--cli", default=DEFAULT_TYPEWHISPER_CLI, help="Path to typewhisper-cli")
    args = parser.parse_args(argv)

    setup_logging()

    cli = resolve_typewhisper_cli(args.cli)
    if cli is None:
        print("TypeWhisper CLI를 찾을 수 없습니다.")
        print(f"기본 경로 확인: {DEFAULT_TYPEWHISPER_CLI}")
        return 1

    status = check_typewhisper_status(cli, args.port, args.api_token)
    if not status["ok"]:
        print("TypeWhisper API 서버에 연결할 수 없습니다.")
        print(status["message"])
        print("TypeWhisper -> Settings -> Advanced -> API Server를 켠 뒤 다시 실행하세요.")
        return 1

    try:
        while True:
            exit_code = run_once(args, cli)
            if not args.loop:
                return exit_code
            print()
            time.sleep(0.4)
    except KeyboardInterrupt:
        print("\n종료합니다.")
        return 0


def resolve_typewhisper_cli(path: str) -> str | None:
    if Path(path).is_file():
        return path
    return shutil.which("typewhisper")


def check_typewhisper_status(cli: str, port: int | None, api_token: str | None) -> dict[str, str | bool]:
    command = [cli, "status", "--json"]
    add_connection_options(command, port, api_token)
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=8)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "message": str(exc)}

    if result.returncode != 0:
        return {"ok": False, "message": (result.stderr or result.stdout).strip()}
    return {"ok": True, "message": result.stdout.strip()}


def run_once(args: argparse.Namespace, cli: str) -> int:
    with tempfile.TemporaryDirectory(prefix="voca-audio-") as tmpdir:
        audio_path = Path(tmpdir) / "command.wav"
        try:
            print(f"녹음: {args.duration:g}초 동안 말하세요.")
            record_wav(audio_path, args.duration, args.sample_rate, args.channels)
            kept_path = keep_audio_file(audio_path) if args.keep_audio else None

            transcript = transcribe_audio(
                cli,
                audio_path,
                port=args.port,
                api_token=args.api_token,
                language=args.language,
                language_hints=args.language_hint,
                engine=args.engine,
                model=args.model,
            )
        except RuntimeError as exc:
            print(f"결과: 실패 - {exc}")
            return 1

        print(f"인식: {transcript}")
        if kept_path:
            print(f"오디오: {kept_path}")
        if not transcript:
            print("결과: 실패 - empty transcript")
            return 1

        intent = parse_intent(transcript)
        print(f"해석: {describe_intent(intent)}")
        logger.info("Voice transcript: %s", transcript)
        logger.info("Parsed intent: %s", intent)

        if args.dry_run:
            print(json.dumps({"ok": True, "dry_run": True, "transcript": transcript, "intent": intent}, ensure_ascii=False))
            return 0

        if not args.allow_text and intent.get("action") == "type_text":
            result = {
                "ok": True,
                "action": "skip_text",
                "message": "plain dictation skipped in voice command mode",
            }
            print(f"결과: {describe_result(result)}")
            print(json.dumps({"transcript": transcript, "intent": intent, "result": result}, ensure_ascii=False))
            return 0

        result = route_intent(intent)
        print(f"결과: {describe_result(result)}")
        logger.info("Action result: %s", result)
        print(json.dumps({"transcript": transcript, "intent": intent, "result": result}, ensure_ascii=False))
        return 0 if result.get("ok") else 1


def record_wav(path: Path, duration: float, sample_rate: int, channels: int) -> None:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise SystemExit("sounddevice가 필요합니다. `pip install -r requirements.txt`를 실행하세요.") from exc

    frames = int(duration * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=channels, dtype="int16")
    sd.wait()

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())


def keep_audio_file(source: Path) -> Path:
    output_dir = Path("logs/audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"voice-{int(time.time() * 1000)}.wav"
    destination.write_bytes(source.read_bytes())
    return destination


def transcribe_audio(
    cli: str,
    audio_path: Path,
    *,
    port: int | None,
    api_token: str | None,
    language: str | None,
    language_hints: list[str],
    engine: str | None,
    model: str | None,
) -> str:
    command = [cli, "transcribe", str(audio_path), "--json", "--await-download"]
    add_connection_options(command, port, api_token)
    if language:
        command.extend(["--language", language])
    for hint in language_hints:
        command.extend(["--language-hint", hint])
    if engine:
        command.extend(["--engine", engine])
    if model:
        command.extend(["--model", model])

    result = subprocess.run(command, text=True, capture_output=True, timeout=90)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())

    return extract_transcript_from_cli_output(result.stdout)


def add_connection_options(command: list[str], port: int | None, api_token: str | None) -> None:
    if port is not None:
        command.extend(["--port", str(port)])
    if api_token:
        command.extend(["--api-token", api_token])


def extract_transcript_from_cli_output(output: str) -> str:
    text = output.strip()
    if not text:
        return ""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text

    if isinstance(data, str):
        return data.strip()
    value = find_text_value(data)
    return value.strip() if value else ""


def find_text_value(value: Any) -> str | None:
    keys = ("text", "transcript", "transcription", "result", "content", "message")
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate
            if isinstance(candidate, (dict, list)):
                nested = find_text_value(candidate)
                if nested:
                    return nested
        for candidate in value.values():
            nested = find_text_value(candidate)
            if nested:
                return nested
    if isinstance(value, list):
        for item in value:
            nested = find_text_value(item)
            if nested:
                return nested
    return None


if __name__ == "__main__":
    raise SystemExit(main())
