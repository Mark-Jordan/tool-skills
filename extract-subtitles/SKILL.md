---
name: extract-subtitles
description: Use when the user asks to extract subtitles from video files, generate SRT or text transcripts, or convert video speech to text. Triggers on requests containing "字幕提取", "提取字幕", "语音转文字", "视频转文字", "生成字幕", "extract subtitles", "transcribe video".
---

# 视频字幕提取

## 概述

先做环境与模型检查，再做转录，最后做语义纠正。

## 执行流程

### 阶段零：前置确认

在开始处理前，先确认两件事：

1. 模型缓存是否存在；不存在则先下载
2. 用户是否有参考输出或参考文档可以用于后续纠正

标准顺序：

1. 确认用户提供的视频目录或视频文件路径是否存在
2. 运行 `--prepare-model-only` 检查并准备模型
3. 询问用户是否有参考输出或参考文档
4. 运行转录脚本生成 `.srt` 和 `.txt`
5. 读取 `.txt`
6. 按参考资料或通用规则做语义纠正
7. 写回 `.txt` 和 `.srt`

不要在没有确认路径存在前直接扫描目录。

### 阶段一：机械转录（Python 脚本）

运行 `subtitle_pipeline.py` 完成模型检查、MP4 → SRT → TXT → 繁转简：

```bash
conda activate tools
python <skill_dir>/subtitle_pipeline.py <视频文件或目录> [--model tiny|base|small|medium] [--language zh|en] [--prepare-model-only]
```

| 参数 | 说明 |
|------|------|
| `input_path` | MP4 视频文件或包含 .mp4 文件的目录（必填） |
| `--model` | 模型大小: tiny/base/small/medium，默认 base |
| `--language` | 音频语言代码，默认 zh |
| `--output-dir` | 输出目录，默认同视频目录 |
| `--no-simplify` | 跳过繁转简 |
| `--prepare-model-only` | 仅检查/下载模型，不扫描视频 |

输出文件（每个视频生成两个）：
- `视频名.srt` — 标准 SRT 字幕
- `视频名.txt` — 纯文本，每行一条画面字幕

首次运行自动从 hf-mirror.com 国内镜像下载模型，缓存于 `<skill_dir>/.whisper_models/`。
若模型已存在，优先复用本地缓存。

### 阶段二：语义纠正（Claude 大模型）

脚本执行完成后，**必须**按以下步骤进行语义纠正：

#### 1. 读取原始文本

用 Read 工具读取阶段一生成的 `.txt` 文件。

#### 2. 询问参考输出/参考文档（必须）

**必须向用户提问：**

> 是否有可参考的输出或资料（例如已知字幕、操作手册、产品说明、术语表）？
> 有的话我可以先对照参考内容，再做更准确的语义纠正。

#### 3. 执行语义纠正

**有参考输出或参考文档时：**
- 优先读取用户提供的参考字幕、术语表、文档或输出样例
- 提取术语、产品名、专有名词、数字模式、流程名
- 逐行对比原始字幕，修正：
  - 同音/近音词错误
  - 专业术语错误
  - 断句/语序问题
  - 数字、字母模式错误

**无参考文档时：**
- 基于通用语言知识进行语义平滑：
  - 修正明显的同音字混淆
  - 修正不通顺的语序
  - 修正明显的繁简混杂
  - 保持原意，不做领域推断

#### 4. 写入纠正结果

将纠正后的文本写回原 `.txt` 和 `.srt` 文件。纠正后的文本应逐行对应原始字幕行（不合并、不拆分）。

#### 5. 模型选择建议

默认仍使用 `faster-whisper` 的 CPU 路线，优先 `base` 或 `small`。若目标机器 CPU 资源较紧，可先保留 `base`，追求更高识别率再切到 `small`。

硬字幕 OCR 是另一条独立路线，只在视频画面里本身带有字幕且音频质量差时考虑，不作为默认流程。

需要评估模型或切换路线时，读取 `references/model-selection.md`。

## 完整示例

```bash
# 基本用法（先准备模型，再转录 + 通用语义纠正）
conda activate tools
python subtitle_pipeline.py "./videos/" --prepare-model-only
python subtitle_pipeline.py "./videos/"
# Claude: 读取输出 → 先询问参考输出/参考文档 → 纠正 → 写回

# 高精度（small 模型 + 参考文档纠正）
python subtitle_pipeline.py "./videos/" --model small
# Claude: 读取输出 → 用户提供 "操作手册.docx" 或参考字幕 → 结合纠正 → 写回

# 英文视频
python subtitle_pipeline.py "./videos/" --language en --no-simplify

# 单个视频
python subtitle_pipeline.py "./videos/demo.mp4"
```

## 常见问题

| 问题 | 解决 |
|------|------|
| SSL 证书错误 | 脚本已内置 certifi 修复 |
| HuggingFace 下载慢 | 已配置 hf-mirror.com 镜像 |
| 转录不准确 | 换 `--model small` 或 `--model medium` |
| GBK 终端乱码 | 文件本身是 UTF-8，直接 Read 工具读取 |
| 模型已下载仍报错 | 检查 `<skill_dir>/.whisper_models/` 目录完整性 |
