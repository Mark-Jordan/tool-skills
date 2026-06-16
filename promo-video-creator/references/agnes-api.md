# Agnes API Reference

Sources verified from Agnes docs on 2026-06-09:

- `https://agnes-ai.com/doc/agnes-image-21-flash`
- `https://agnes-ai.com/doc/agnes-video-v20`
- `https://agnes-ai.com/doc/agnes-20-flash`
- `https://agnes-ai.com/doc#3764a189-eee5-801e-8031-ce764321a598` (`cid8`, Codex++ integration)

## Auth And Base URLs

- API gateway: `https://apihub.agnes-ai.com`
- OpenAI-compatible base URL for chat tools: `https://apihub.agnes-ai.com/v1`
- Header: `Authorization: Bearer YOUR_API_KEY`
- Content type: `application/json`
- For provider UIs, enter only the `sk-...` key, without the `Bearer` prefix.

The helper script reads credentials in this order:

1. Process environment variables: `AGNES_API_KEY`, `AGNES_KEY`, then `API_KEY`.
2. File path from `AGNES_CREDENTIALS_FILE`, if set.
3. `~/.config/agnes/credentials.env`.
4. `~/.agnes/credentials.env`.
5. Current working directory `.env`, only as a local fallback.

Prefer `AGNES_API_KEY` in `~/.config/agnes/credentials.env` for clarity. Do not place secrets inside the skill folder.

Use the helper to inspect or create configuration:

```bash
python scripts/agnes_api.py config
python scripts/agnes_api.py config --set-key sk-your-agnes-key
```

## Image: Agnes Image 2.1 Flash

- Model: `agnes-image-2.1-flash`
- Endpoint: `POST https://apihub.agnes-ai.com/v1/images/generations`
- Supports text-to-image and image-to-image.
- Required text-to-image fields: `model`, `prompt`, `size`.
- Image-to-image input: place public URLs or Data URI Base64 values in `extra_body.image`.
- URL output: `extra_body.response_format: "url"`, returned at `data[0].url`.
- Text-to-image Base64 output: `return_base64: true`, returned at `data[0].b64_json`.
- Image-to-image Base64 output: `extra_body.response_format: "b64_json"`, returned at `data[0].b64_json`.

Text-to-image URL output:

```json
{
  "model": "agnes-image-2.1-flash",
  "prompt": "A luminous floating city above a misty canyon at sunrise, cinematic realism",
  "size": "1024x768",
  "extra_body": {
    "response_format": "url"
  }
}
```

Image-to-image URL output:

```json
{
  "model": "agnes-image-2.1-flash",
  "prompt": "Transform the scene into a rain-soaked cyberpunk night while preserving the original composition",
  "size": "1024x768",
  "extra_body": {
    "image": [
      "https://example.com/input-image.png"
    ],
    "response_format": "url"
  }
}
```

Common pitfalls:

- Do not put `response_format` at top level.
- Do not pass `tags: ["img2img"]`.
- Input image URLs must be public and accessible without cookies or private headers.
- Recommended timeout: `60s` to `360s`.

## Video: Agnes Video V2.0

- Model: `agnes-video-v2.0`
- Create task: `POST https://apihub.agnes-ai.com/v1/videos`
- Recommended result query: `GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>`
- Legacy result query: `GET https://apihub.agnes-ai.com/v1/videos/<TASK_ID>`
- Final video URL field: `remixed_from_video_id`.
- Status values: `queued`, `in_progress`, `completed`, `failed`.

Create task fields:

- `model` required, use `agnes-video-v2.0`.
- `prompt` required.
- `image` optional string for single image-to-video.
- `extra_body.image` optional array for multi-image/keyframes.
- `extra_body.mode: "keyframes"` for keyframe animation.
- `height` default `768`.
- `width` default `1152`.
- `num_frames` must be `8n + 1` and `<= 441`.
- `frame_rate` supports `1` to `60`.
- `seed`, `num_inference_steps`, `negative_prompt` are optional.

Common durations at 24 FPS:

- About 3 seconds: `num_frames: 81`
- About 5 seconds: `num_frames: 121`
- About 10 seconds: `num_frames: 241`
- About 18 seconds: `num_frames: 441`

Text-to-video:

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "A cinematic shot of a cat walking on the beach at sunset, soft ocean waves, warm golden lighting, realistic motion",
  "height": 768,
  "width": 1152,
  "num_frames": 121,
  "frame_rate": 24
}
```

Image-to-video:

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "The woman slowly turns around and looks back at the camera, natural expression, cinematic camera movement",
  "image": "https://example.com/image.png",
  "num_frames": 121,
  "frame_rate": 24
}
```

Multi-image/keyframe:

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "Create a smooth cinematic transition between the keyframes, maintaining visual consistency and natural motion",
  "extra_body": {
    "image": [
      "https://example.com/keyframe1.png",
      "https://example.com/keyframe2.png"
    ],
    "mode": "keyframes"
  },
  "num_frames": 121,
  "frame_rate": 24
}
```

## Text Helper: Agnes 2.0 Flash

- Model: `agnes-2.0-flash`
- Endpoint: `POST https://apihub.agnes-ai.com/v1/chat/completions`
- Use for lightweight tasks only: prompt polishing, short variants, negative prompt suggestions, simple captions, simple extraction.
- Required fields: `model`, `messages`.
- Supports `temperature`, `top_p`, `max_tokens`, `stream`, `tools`, `tool_choice`.
- Supports image URL inputs in `messages[].content` arrays.

Basic request:

```json
{
  "model": "agnes-2.0-flash",
  "messages": [
    {
      "role": "system",
      "content": "You rewrite user ideas into concise production prompts."
    },
    {
      "role": "user",
      "content": "Make this into an image prompt: glowing city in fog"
    }
  ],
  "temperature": 0.4,
  "max_tokens": 512
}
```
