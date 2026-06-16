import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "voicertool_tts.py"
spec = importlib.util.spec_from_file_location("voicertool_tts", SCRIPT_PATH)
voicertool_tts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voicertool_tts)


def test_default_options_use_chinese_yunyang():
    args = voicertool_tts.build_parser().parse_args(["--text", "你好", "--dry-run"])

    assert args.language == "zh-CN"
    assert args.voice == "zh-CN-YunyangNeural"
    assert args.pitch == "0%"
    assert args.rate == "0%"
    assert args.volume == "100%"


def test_ssml_escapes_text_and_applies_prosody():
    ssml = voicertool_tts.build_ssml(
        "A & B < C",
        voice="zh-CN-YunyangNeural",
        pitch="+5%",
        rate="-10%",
        volume="80%",
    )

    assert "Microsoft Server Speech Text to Speech Voice (zh-CN, YunyangNeural)" in ssml
    assert "A &amp; B &lt; C" in ssml
    assert 'pitch="+5%"' in ssml
    assert 'rate="-10%"' in ssml
    assert 'volume="80%"' in ssml


def test_filter_voices_by_language_and_query():
    voices = [
        {"ShortName": "zh-CN-YunyangNeural", "Locale": "zh-CN", "FriendlyName": "Yunyang"},
        {"ShortName": "en-US-AvaMultilingualNeural", "Locale": "en-US", "FriendlyName": "Ava"},
    ]

    filtered = voicertool_tts.filter_voices(voices, language="zh-CN", query="yun")

    assert [voice["ShortName"] for voice in filtered] == ["zh-CN-YunyangNeural"]


def test_dry_run_prints_request_payload(capsys):
    rc = voicertool_tts.main(["--text", "你好", "--dry-run"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["voice"] == "zh-CN-YunyangNeural"
    assert payload["language"] == "zh-CN"
    assert payload["text"] == "你好"
