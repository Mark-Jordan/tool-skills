#!/usr/bin/env python3
"""Voicertool-compatible text-to-speech helper.

The website uses Microsoft Edge Read Aloud voices in the browser. This script
uses the same public voice list and WebSocket synthesis flow for local audio
generation.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import secrets
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import requests
import websocket


TRUSTED_CLIENT_TOKEN = "6A5AA1D4EAFF4E9FB37E23D68491D6F4"
SEC_MS_GEC_VERSION = "1-145.0.38"
CHROMIUM_FULL_VERSION = "143.0.3650.75"
CHROMIUM_MAJOR_VERSION = CHROMIUM_FULL_VERSION.split(".", maxsplit=1)[0]
EDGE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    f"(KHTML, like Gecko) Chrome/{CHROMIUM_MAJOR_VERSION}.0.0.0 Safari/537.36 "
    f"Edg/{CHROMIUM_MAJOR_VERSION}.0.0.0"
)
VOICE_LIST_URL = (
    "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list"
    f"?trustedclienttoken={TRUSTED_CLIENT_TOKEN}"
)
SYNTHESIS_URL = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1"
DEFAULT_LANGUAGE = "zh-CN"
DEFAULT_VOICE = "zh-CN-YunyangNeural"
DEFAULT_OUTPUT = "output/audio/voiceover.mp3"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate MP3 speech using the Voicertool/Edge Read Aloud voice service."
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--text", help="Text to synthesize.")
    input_group.add_argument("--text-file", help="UTF-8 text file to synthesize.")
    parser.add_argument("--out", default=DEFAULT_OUTPUT, help=f"Output MP3 path. Default: {DEFAULT_OUTPUT}")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help=f"Voice locale. Default: {DEFAULT_LANGUAGE}")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"Voice short name. Default: {DEFAULT_VOICE}")
    parser.add_argument("--pitch", default="0%", help='Pitch adjustment, e.g. "0%%", "+5%%", "-10%%".')
    parser.add_argument("--rate", default="0%", help='Speaking rate adjustment, e.g. "0%%", "+10%%", "-15%%".')
    parser.add_argument("--volume", default="100%", help='Volume adjustment, e.g. "100%%", "80%%".')
    parser.add_argument("--list-languages", action="store_true", help="List available locales and voice counts.")
    parser.add_argument("--list-voices", action="store_true", help="List available voices.")
    parser.add_argument("--voice-query", help="Filter voices by name, short name, locale, or friendly name.")
    parser.add_argument("--timeout", type=int, default=30, help="Network timeout in seconds. Default: 30.")
    parser.add_argument("--dry-run", action="store_true", help="Print request payload and SSML without synthesis.")
    return parser


def read_text(text: str | None, text_file: str | None) -> str:
    if text_file:
        path = Path(text_file)
        if not path.exists():
            raise SystemExit(f"Text file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    if text is not None:
        return text.strip()
    raise SystemExit("Specify --text, --text-file, --list-languages, or --list-voices.")


def fetch_voices(timeout: int = 30) -> list[dict[str, Any]]:
    response = requests.get(VOICE_LIST_URL, timeout=timeout)
    response.raise_for_status()
    voices = response.json()
    if not isinstance(voices, list):
        raise SystemExit("Unexpected voice list response.")
    return voices


def filter_voices(
    voices: list[dict[str, Any]],
    language: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    result = voices
    if language:
        language_lower = language.lower()
        result = [voice for voice in result if str(voice.get("Locale", "")).lower() == language_lower]
    if query:
        query_lower = query.lower()
        searchable_keys = ("ShortName", "Name", "FriendlyName", "LocalName", "Locale", "Gender")
        result = [
            voice
            for voice in result
            if any(query_lower in str(voice.get(key, "")).lower() for key in searchable_keys)
        ]
    return result


def print_languages(voices: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for voice in voices:
        locale = str(voice.get("Locale", "unknown"))
        counts[locale] = counts.get(locale, 0) + 1
    print(f"Available languages/locales: {len(counts)}")
    for locale in sorted(counts):
        print(f"{locale}\t{counts[locale]}")


def print_voices(voices: list[dict[str, Any]]) -> None:
    print(f"Available voices: {len(voices)}")
    for voice in voices:
        short_name = voice.get("ShortName", "")
        locale = voice.get("Locale", "")
        gender = voice.get("Gender", "")
        friendly = voice.get("FriendlyName") or voice.get("LocalName") or voice.get("Name", "")
        print(f"{short_name}\t{locale}\t{gender}\t{friendly}")


def normalize_voice_name(voice: str) -> str:
    parts = voice.split("-")
    if len(parts) >= 3 and voice.endswith("Neural"):
        lang = parts[0]
        region = parts[1]
        name = "-".join(parts[2:])
        return f"Microsoft Server Speech Text to Speech Voice ({lang}-{region}, {name})"
    return voice


def build_ssml(
    text: str,
    voice: str,
    pitch: str,
    rate: str,
    volume: str,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    escaped_text = html.escape(text, quote=False)
    voice_name = normalize_voice_name(voice)
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{language}">'
        f'<voice name="{voice_name}">'
        f'<prosody pitch="{pitch}" rate="{rate}" volume="{volume}">'
        f"{escaped_text}"
        "</prosody>"
        "</voice>"
        "</speak>"
    )


def sec_ms_gec() -> str:
    ticks = time.time() + 11644473600
    ticks -= ticks % 300
    ticks *= 10_000_000
    payload = f"{int(ticks)}{TRUSTED_CLIENT_TOKEN}"
    return hashlib.sha256(payload.encode("ascii")).hexdigest().upper()


def websocket_url(connection_id: str) -> str:
    return (
        f"{SYNTHESIS_URL}?TrustedClientToken={TRUSTED_CLIENT_TOKEN}"
        f"&ConnectionId={connection_id}"
        f"&Sec-MS-GEC={sec_ms_gec()}"
        f"&Sec-MS-GEC-Version={SEC_MS_GEC_VERSION}"
    )


def message(headers: dict[str, str], body: str) -> str:
    lines = [f"{key}:{value}" for key, value in headers.items()]
    return "\r\n".join(lines) + "\r\n\r\n" + body


def synthesize(
    text: str,
    voice: str,
    pitch: str,
    rate: str,
    volume: str,
    language: str,
    timeout: int = 30,
) -> bytes:
    connection_id = uuid.uuid4().hex
    headers = [
        "Pragma: no-cache",
        "Cache-Control: no-cache",
        "Origin: chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold",
        f"User-Agent: {EDGE_USER_AGENT}",
        "Accept-Encoding: gzip, deflate, br, zstd",
        "Accept-Language: en-US,en;q=0.9",
        f"Cookie: muid={secrets.token_hex(16).upper()};",
    ]
    ws = websocket.create_connection(
        websocket_url(connection_id),
        timeout=timeout,
        header=headers,
    )
    try:
        timestamp = time.strftime("%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)", time.gmtime())
        config = json.dumps(
            {
                "context": {
                    "synthesis": {
                        "audio": {
                            "metadataoptions": {
                                "sentenceBoundaryEnabled": False,
                                "wordBoundaryEnabled": True,
                            },
                            "outputFormat": "audio-24khz-48kbitrate-mono-mp3",
                        }
                    }
                }
            },
            separators=(",", ":"),
        )
        ws.send(
            message(
                {
                    "Content-Type": "application/json; charset=utf-8",
                    "Path": "speech.config",
                    "X-Timestamp": timestamp,
                },
                config,
            )
        )
        ws.send(
            message(
                {
                    "Content-Type": "application/ssml+xml",
                    "Path": "ssml",
                    "X-RequestId": connection_id,
                    "X-Timestamp": timestamp,
                },
                build_ssml(text, voice, pitch, rate, volume, language),
            )
        )

        audio = bytearray()
        while True:
            frame = ws.recv()
            if isinstance(frame, str):
                if "Path:turn.end" in frame:
                    break
                continue
            if not frame:
                continue
            header_length = int.from_bytes(frame[:2], byteorder="big", signed=True)
            audio.extend(frame[2 + header_length :])
        return bytes(audio)
    finally:
        ws.close()


def validate_voice(voices: list[dict[str, Any]], voice: str, language: str) -> None:
    if any(item.get("ShortName") == voice for item in voices):
        return
    matches = filter_voices(voices, language=language, query=voice)
    if matches:
        examples = ", ".join(str(item.get("ShortName")) for item in matches[:10])
        raise SystemExit(f"Voice must use ShortName. Did you mean one of: {examples}")
    raise SystemExit(f"Voice not found: {voice}. Run --list-voices --language {language}.")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_languages or args.list_voices:
        voices = fetch_voices(timeout=args.timeout)
        if args.list_languages:
            print_languages(voices)
        if args.list_voices:
            print_voices(filter_voices(voices, language=args.language, query=args.voice_query))
        return 0

    text = read_text(args.text, args.text_file)
    payload = {
        "text": text,
        "language": args.language,
        "voice": args.voice,
        "pitch": args.pitch,
        "rate": args.rate,
        "volume": args.volume,
        "out": args.out,
        "ssml": build_ssml(text, args.voice, args.pitch, args.rate, args.volume, args.language),
    }
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    voices = fetch_voices(timeout=args.timeout)
    validate_voice(voices, args.voice, args.language)
    audio = synthesize(text, args.voice, args.pitch, args.rate, args.volume, args.language, timeout=args.timeout)
    if not audio:
        raise SystemExit("No audio data returned.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    print(str(out.resolve()))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())
