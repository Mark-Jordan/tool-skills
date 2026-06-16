#!/usr/bin/env python
"""
视频字幕提取脚本（仅负责转录和格式转换，不含语义纠正）
========================================================
流程: 模型检查 → MP4查找 → 音频提取 → faster-whisper转录 → SRT字幕 → 纯文本 → 繁转简

语义纠正由调用方（Claude大模型）在脚本执行完成后处理。

依赖: faster-whisper, zhconv, imageio-ffmpeg(自带)
环境: conda activate tools

用法:
    python subtitle_pipeline.py /path/to/videos/              # 基本用法
    python subtitle_pipeline.py /path/to/videos/ --model small # 指定模型
    python subtitle_pipeline.py /path/to/videos/ --language en # 英文（跳过繁转简）
    python subtitle_pipeline.py /path/to/videos/ --output-dir ./out/  # 指定输出目录
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── SSL 修复（Windows + conda 常见问题） ──
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

# 国内 HuggingFace 镜像
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


def find_videos(input_path: Path) -> list[Path]:
    """根据输入路径查找 MP4 视频文件"""
    if input_path.is_file():
        if input_path.suffix.lower() != ".mp4":
            raise ValueError(f"输入文件不是 MP4: {input_path}")
        return [input_path]

    videos = sorted(input_path.glob("*.mp4"))
    if not videos:
        raise FileNotFoundError(f"目录下未找到 MP4 文件: {input_path}")
    return videos


def get_cached_model_path(model_size: str, cache_dir: Path) -> Optional[str]:
    """返回已缓存的 faster-whisper 模型路径；不存在时返回 None"""
    models_root = cache_dir / f"models--Systran--faster-whisper-{model_size}"
    snapshots_dir = models_root / "snapshots"
    if not snapshots_dir.exists():
        return None

    snapshots = sorted(p for p in snapshots_dir.iterdir() if p.is_dir())
    if not snapshots:
        return None
    return str(snapshots[-1])


def ensure_model(model_size: str, cache_dir: Path) -> str:
    """检查 faster-whisper 模型缓存；不存在时从镜像下载"""
    from huggingface_hub import snapshot_download

    cached_model = get_cached_model_path(model_size, cache_dir)
    if cached_model:
        print(f"[模型] 已存在: {cached_model}")
        return cached_model

    repo_id = f"Systran/faster-whisper-{model_size}"
    print(f"[模型] 未找到本地缓存，开始下载 {repo_id} (镜像: hf-mirror.com)...")

    downloaded_path = snapshot_download(repo_id, cache_dir=str(cache_dir))

    cached_model = get_cached_model_path(model_size, cache_dir)
    return cached_model or downloaded_path


def _get_ffmpeg() -> str:
    """获取 imageio-ffmpeg 自带的 FFmpeg 二进制路径"""
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _extract_audio(video_path: Path, work_dir: Path) -> Path:
    """提取视频音频到临时 WAV（纯 ASCII 路径，避免 PyAV 中文路径问题）"""
    safe_name = f"audio_{abs(hash(str(video_path)))}.wav"
    audio_path = work_dir / safe_name
    if audio_path.exists():
        return audio_path

    ffmpeg = _get_ffmpeg()
    subprocess.run(
        [ffmpeg, "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
         "-ar", "16000", "-ac", "1", str(audio_path), "-y"],
        capture_output=True, check=True,
    )
    return audio_path


def transcribe_videos(
    videos: list[Path],
    model_path: str,
    output_dir: Path,
    language: str = "zh",
) -> list[Path]:
    """转录视频 → 生成 SRT 文件，返回 SRT 路径列表"""
    from faster_whisper import WhisperModel

    print(f"[加载] 本地模型: {model_path}")
    model = WhisperModel(
        model_path, device="cpu", compute_type="int8",
        num_workers=2, local_files_only=True,
    )

    srt_files = []
    for video in videos:
        srt_path = output_dir / video.with_suffix(".srt").name
        print(f"\n{'='*50}")
        print(f"[转录] {video.name}")

        tmp_audio = _extract_audio(video, output_dir)
        print(f"[音频] {tmp_audio.stat().st_size / 1024:.0f} KB")

        segments, info = model.transcribe(
            str(tmp_audio), beam_size=5, vad_filter=True, language=language,
        )
        print(f"[语言] {info.language} (置信度: {info.language_probability:.2%})")

        entries = []
        for i, seg in enumerate(segments, 1):
            t0 = _fmt_time(seg.start)
            t1 = _fmt_time(seg.end)
            text = seg.text.strip()
            entries.append(f"{i}\n{t0} --> {t1}\n{text}\n")
            if i <= 2 or i % 20 == 0:
                print(f"  [{t0}] {text}")

        srt_path.write_text("\n".join(entries), encoding="utf-8")
        print(f"[完成] {len(entries)} 条字幕 → {srt_path.name}")
        srt_files.append(srt_path)
        tmp_audio.unlink(missing_ok=True)

    return srt_files


def srt_to_text(srt_files: list[Path]) -> list[Path]:
    """SRT → 纯文本（每行一条画面字幕），返回 txt 路径列表"""
    txt_files = []
    for srt in srt_files:
        txt_path = srt.with_suffix(".txt")
        content = srt.read_text(encoding="utf-8")
        lines = []
        for block in content.strip().split("\n\n"):
            parts = block.strip().split("\n")
            if len(parts) >= 3:
                text = " ".join(parts[2:]).strip()
                if text:
                    lines.append(text)
        txt_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"[文本] {srt.name} → {txt_path.name} ({len(lines)} 行)")
        txt_files.append(txt_path)
    return txt_files


def convert_to_simplified(files: list[Path]) -> None:
    """繁体中文 → 简体中文（原地修改）"""
    import zhconv
    for f in files:
        content = f.read_text(encoding="utf-8")
        converted = zhconv.convert(content, "zh-cn")
        f.write_text(converted, encoding="utf-8")
        print(f"[简转] {f.name}")


def _fmt_time(seconds: float) -> str:
    """秒数 → SRT 时间戳 HH:MM:SS,mmm"""
    h, m = divmod(int(seconds), 3600)
    m, s = divmod(m, 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    parser = argparse.ArgumentParser(description="视频字幕提取（转录+格式转换）")
    parser.add_argument("input_path", type=Path, help="MP4 视频文件或包含 MP4 视频的目录")
    parser.add_argument("--model", default="base",
                        choices=["tiny", "base", "small", "medium"],
                        help="whisper 模型大小 (默认: base)")
    parser.add_argument("--language", default="zh", help="音频语言代码 (默认: zh)")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="输出目录 (默认: 视频所在目录)")
    parser.add_argument("--no-simplify", action="store_true", help="跳过繁转简")
    parser.add_argument("--cache-dir", type=Path,
                        default=Path(__file__).parent / ".whisper_models",
                        help="模型缓存目录")
    parser.add_argument("--prepare-model-only", action="store_true",
                        help="只检查/下载模型，不扫描或转录视频")
    args = parser.parse_args()

    input_path = args.input_path.resolve()
    if not input_path.exists():
        sys.exit(f"[错误] 路径不存在: {input_path}")
    default_output_dir = input_path.parent if input_path.is_file() else input_path
    output_dir = (args.output_dir or default_output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: 检查/下载模型 ──
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    model_path = ensure_model(args.model, args.cache_dir)
    if args.prepare_model_only:
        print(f"[完成] 模型已就绪: {model_path}")
        return

    # ── Step 2: 查找视频 ──
    videos = find_videos(input_path)
    print(f"[扫描] 找到 {len(videos)} 个视频:")
    for v in videos:
        print(f"  - {v.name} ({v.stat().st_size / 1024**2:.1f} MB)")

    # ── Step 3: 转录 → SRT ──
    srt_files = transcribe_videos(videos, model_path, output_dir, args.language)

    # ── Step 4: SRT → TXT ──
    txt_files = srt_to_text(srt_files)
    all_outputs = srt_files + txt_files

    # ── Step 5: 繁转简 ──
    if not args.no_simplify and args.language == "zh":
        convert_to_simplified(all_outputs)

    # ── 汇总 ──
    print(f"\n{'='*50}")
    print(f"[汇总] 转录完成! 模型={args.model}, 视频={len(videos)}个")
    for f in all_outputs:
        print(f"  → {f}")
    print(f"{'='*50}")
    print(f"[下一步] 由 Claude 对上述文本进行语义纠正 (参考 SKILL.md)")


if __name__ == "__main__":
    main()
