#!/usr/bin/env python3
"""Small Agnes API helper for image, video, and lightweight text tasks."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "https://apihub.agnes-ai.com"
IMAGE_MODEL = "agnes-image-2.1-flash"
VIDEO_MODEL = "agnes-video-v2.0"
TEXT_MODEL = "agnes-2.0-flash"
KEY_NAMES = ("AGNES_API_KEY", "AGNES_KEY", "API_KEY")


def credential_paths() -> list[Path]:
    paths: list[Path] = []
    override = os.environ.get("AGNES_CREDENTIALS_FILE")
    if override:
        paths.append(Path(override).expanduser())
    home = Path.home()
    paths.extend(
        [
            home / ".config" / "agnes" / "credentials.env",
            home / ".agnes" / "credentials.env",
            Path.cwd() / ".env",
        ]
    )
    return paths


def default_credentials_path() -> Path:
    return Path.home() / ".config" / "agnes" / "credentials.env"


def load_dotenv() -> None:
    env_path = next((path for path in credential_paths() if path.exists()), None)
    if env_path is None:
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def find_configured_key() -> tuple[str | None, str | None]:
    for name in KEY_NAMES:
        if os.environ.get(name):
            return name, "environment"
    for path in credential_paths():
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in KEY_NAMES and value:
                return key, str(path)
    return None, None


def api_key() -> str:
    load_dotenv()
    key = os.environ.get("AGNES_API_KEY") or os.environ.get("AGNES_KEY") or os.environ.get("API_KEY")
    if not key:
        raise SystemExit(
            "Missing API key. Set AGNES_API_KEY, AGNES_KEY, or API_KEY in the environment, "
            "AGNES_CREDENTIALS_FILE, ~/.config/agnes/credentials.env, ~/.agnes/credentials.env, "
            "or a local .env file."
        )
    return key


def config_command(args: argparse.Namespace) -> None:
    target = Path(args.path).expanduser() if args.path else default_credentials_path()
    if args.set_key:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"AGNES_API_KEY={args.set_key.strip()}\n", encoding="utf-8")
        print(f"Wrote Agnes credentials to: {target}")
        print("Stored variable: AGNES_API_KEY")
        return

    key_name, source = find_configured_key()
    print("Agnes credential configuration")
    print(f"Recommended file: {default_credentials_path()}")
    print("Recommended variable: AGNES_API_KEY")
    print("Accepted variables: AGNES_API_KEY, AGNES_KEY, API_KEY")
    print("Override file env: AGNES_CREDENTIALS_FILE")
    if key_name and source:
        print(f"Detected: yes ({key_name} from {source})")
    else:
        print("Detected: no")
        print(f"Create it with: python {Path(__file__).name} config --set-key sk-your-agnes-key")


def request_json(method: str, url: str, body: dict | None = None, timeout: int = 360) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Network error: {exc}") from exc
    return json.loads(payload)


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https", "data"}


def file_to_data_uri(path_value: str) -> str:
    path = Path(path_value)
    if not path.exists():
        raise SystemExit(f"Input image not found: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def normalize_image(value: str) -> str:
    return value if is_url(value) else file_to_data_uri(value)


def normalize_image_for_dry_run(value: str) -> str:
    return value if is_url(value) else f"data:image/*;base64,<encoded local file: {value}>"


def download_url(url: str, out: Path, timeout: int = 360) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "agnes-creator/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        out.write_bytes(response.read())


def write_b64(value: str, out: Path) -> None:
    if value.startswith("data:"):
        value = value.split(",", 1)[1]
    out.write_bytes(base64.b64decode(value))


def image_command(args: argparse.Namespace) -> None:
    if args.image and args.return_base64:
        raise SystemExit("For image-to-image Base64 output, use --response-format b64_json instead of --return-base64.")

    requested_format = args.response_format
    if requested_format is None and not (args.return_base64 and not args.image):
        requested_format = "url"

    extra_body: dict = {}
    if args.image:
        normalizer = normalize_image_for_dry_run if args.dry_run else normalize_image
        extra_body["image"] = [normalizer(item) for item in args.image]
    if requested_format:
        extra_body["response_format"] = requested_format

    body: dict = {
        "model": IMAGE_MODEL,
        "prompt": args.prompt,
        "size": args.size,
    }
    if extra_body:
        body["extra_body"] = extra_body
    if args.return_base64:
        body["return_base64"] = True

    if args.dry_run:
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return

    result = request_json("POST", f"{BASE_URL}/v1/images/generations", body, timeout=args.timeout)
    item = (result.get("data") or [{}])[0]
    out = Path(args.out) if args.out else None
    if out and item.get("url"):
        download_url(item["url"], out, timeout=args.timeout)
        print(str(out.resolve()))
    elif out and item.get("b64_json"):
        write_b64(item["b64_json"], out)
        print(str(out.resolve()))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


def frames_for_seconds(seconds: float, frame_rate: int) -> int:
    desired = max(1, round(seconds * frame_rate))
    frame = ((desired - 1) // 8) * 8 + 1
    if frame < desired:
        frame += 8
    return min(frame, 441)


def video_result(video_id: str, model_name: str | None, timeout: int) -> dict:
    query = {"video_id": video_id}
    if model_name:
        query["model_name"] = model_name
    url = f"{BASE_URL}/agnesapi?{urllib.parse.urlencode(query)}"
    return request_json("GET", url, timeout=timeout)


def video_command(args: argparse.Namespace) -> None:
    num_frames = args.num_frames or frames_for_seconds(args.seconds, args.frame_rate)
    if num_frames > 441 or (num_frames - 1) % 8 != 0:
        raise SystemExit("num_frames must be <= 441 and follow the 8n + 1 rule.")

    body: dict = {
        "model": VIDEO_MODEL,
        "prompt": args.prompt,
        "height": args.height,
        "width": args.width,
        "num_frames": num_frames,
        "frame_rate": args.frame_rate,
    }
    if args.image and len(args.image) == 1 and not args.keyframes:
        normalizer = normalize_image_for_dry_run if args.dry_run else normalize_image
        body["image"] = normalizer(args.image[0])
    elif args.image:
        normalizer = normalize_image_for_dry_run if args.dry_run else normalize_image
        body["extra_body"] = {"image": [normalizer(item) for item in args.image]}
    if args.keyframes:
        body.setdefault("extra_body", {})["mode"] = "keyframes"
    if args.negative_prompt:
        body["negative_prompt"] = args.negative_prompt
    if args.seed is not None:
        body["seed"] = args.seed

    if args.dry_run:
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return

    created = request_json("POST", f"{BASE_URL}/v1/videos", body, timeout=args.timeout)
    video_id = created.get("video_id")
    if not video_id:
        print(json.dumps(created, indent=2, ensure_ascii=False))
        raise SystemExit("Create response did not include video_id.")

    deadline = time.time() + args.poll_timeout
    last = created
    while time.time() < deadline:
        last = video_result(video_id, VIDEO_MODEL, timeout=args.timeout)
        status = str(last.get("status", "")).lower()
        progress = last.get("progress")
        print(f"status={status or 'unknown'} progress={progress}", file=sys.stderr)
        if status == "completed":
            url = last.get("remixed_from_video_id")
            if args.out and url:
                out = Path(args.out)
                download_url(url, out, timeout=args.timeout)
                print(str(out.resolve()))
            else:
                print(json.dumps(last, indent=2, ensure_ascii=False))
            return
        if status == "failed":
            print(json.dumps(last, indent=2, ensure_ascii=False))
            raise SystemExit("Video generation failed.")
        time.sleep(args.poll_interval)

    print(json.dumps(last, indent=2, ensure_ascii=False))
    raise SystemExit("Timed out waiting for video completion.")


def text_command(args: argparse.Namespace) -> None:
    body = {
        "model": TEXT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": args.system,
            },
            {
                "role": "user",
                "content": args.prompt,
            },
        ],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.dry_run:
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return
    result = request_json("POST", f"{BASE_URL}/v1/chat/completions", body, timeout=args.timeout)
    content = (((result.get("choices") or [{}])[0]).get("message") or {}).get("content")
    print(content if content is not None else json.dumps(result, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agnes AI image/video/text helper")
    sub = parser.add_subparsers(dest="command", required=True)

    config = sub.add_parser("config", help="Show or write user-level Agnes API key configuration")
    config.add_argument("--set-key", help="Write this key to the user-level credentials file. The key is not printed.")
    config.add_argument("--path", help="Custom credentials file path for --set-key.")
    config.set_defaults(func=config_command)

    image = sub.add_parser("image", help="Generate or edit an image")
    image.add_argument("--prompt", required=True)
    image.add_argument("--size", default="1024x768")
    image.add_argument("--image", action="append", help="Input image URL, Data URI, or local file. Repeat for multiple.")
    image.add_argument("--response-format", choices=["url", "b64_json"])
    image.add_argument("--return-base64", action="store_true")
    image.add_argument("--out")
    image.add_argument("--timeout", type=int, default=360)
    image.add_argument("--dry-run", action="store_true")
    image.set_defaults(func=image_command)

    video = sub.add_parser("video", help="Create and poll a video task")
    video.add_argument("--prompt", required=True)
    video.add_argument("--image", action="append", help="Input image URL, Data URI, or local file. Repeat for multiple.")
    video.add_argument("--keyframes", action="store_true")
    video.add_argument("--seconds", type=float, default=5.0)
    video.add_argument("--num-frames", type=int)
    video.add_argument("--frame-rate", type=int, default=24)
    video.add_argument("--height", type=int, default=768)
    video.add_argument("--width", type=int, default=1152)
    video.add_argument("--negative-prompt")
    video.add_argument("--seed", type=int)
    video.add_argument("--out")
    video.add_argument("--timeout", type=int, default=360)
    video.add_argument("--poll-timeout", type=int, default=1800)
    video.add_argument("--poll-interval", type=int, default=10)
    video.add_argument("--dry-run", action="store_true")
    video.set_defaults(func=video_command)

    text = sub.add_parser("text", help="Lightweight text helper")
    text.add_argument("--prompt", required=True)
    text.add_argument("--system", default="You are a concise prompt assistant for image and video generation. Keep answers short and directly usable.")
    text.add_argument("--temperature", type=float, default=0.4)
    text.add_argument("--max-tokens", type=int, default=512)
    text.add_argument("--timeout", type=int, default=120)
    text.add_argument("--dry-run", action="store_true")
    text.set_defaults(func=text_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
