---
name: extract-subtitles
description: Use when the user asks to extract subtitles from video files, generate SRT or text transcripts, or convert video speech to text. Triggers on requests containing "字幕提取", "提取字幕", "语音转文字", "视频转文字", "生成字幕", "extract subtitles", "transcribe video".
---

# 视频字幕提取

## 概述

两阶段流程：**Python 脚本**负责转录 + 格式转换，**Claude 大模型**负责语义纠正。

## 执行流程

### 阶段一：机械转录（Python 脚本）

运行 `subtitle_pipeline.py` 完成 MP4 → SRT → TXT → 繁转简：

```bash
conda activate tools
python <skill_dir>/subtitle_pipeline.py <视频目录> [--model base|small|medium] [--language zh|en]
```

| 参数 | 说明 |
|------|------|
| `directory` | 包含 .mp4 文件的目录（必填） |
| `--model` | 模型大小: tiny/base/small/medium，默认 base |
| `--language` | 音频语言代码，默认 zh |
| `--output-dir` | 输出目录，默认同视频目录 |
| `--no-simplify` | 跳过繁转简 |

输出文件（每个视频生成两个）：
- `视频名.srt` — 标准 SRT 字幕
- `视频名.txt` — 纯文本，每行一条画面字幕

首次运行自动从 hf-mirror.com 国内镜像下载模型，缓存于 `<skill_dir>/.whisper_models/`。

### 阶段二：语义纠正（Claude 大模型）

脚本执行完成后，**必须**按以下步骤进行语义纠正：

#### 1. 读取原始文本

用 Read 工具读取阶段一生成的 `.txt` 文件。

#### 2. 询问参考文档（必须）

**必须向用户提问：**

> 是否有与视频内容相关的参考文档（如操作手册、产品说明、术语表等）？
> 有的话我可以结合文档中的专业术语和语境对字幕进行更精准的语义纠正。

#### 3. 执行语义纠正

**有参考文档时：**
- 读取用户提供的参考文档（.docx / .pdf / .txt）
- 提取文档中的专业术语、产品名、流程描述等作为纠错依据
- 逐行对比原始字幕，修正：
  - 同音/近音词错误 → 根据文档术语推断正确写法
  - 专业术语错误 → 替换为文档中的标准术语
  - 断句/语序问题 → 结合文档语境调整
  - 数字、字母模式错误（如 "三干元" → "三千元"、"A方案"被识别为"iPhone案"）

**无参考文档时：**
- 基于通用语言知识进行语义平滑：
  - 修正明显的同音字混淆
  - 修正不通顺的语序
  - 修正明显的繁简混杂
  - 保持原意，不做领域推断

#### 4. 写入纠正结果

将纠正后的文本写回原 `.txt` 和 `.srt` 文件。纠正后的文本应逐行对应原始字幕行（不合并、不拆分）。

## 完整示例

```bash
# 基本用法（转录 + 通用语义纠正）
conda activate tools
python subtitle_pipeline.py "./videos/"
# Claude: 读取输出 → 询问参考文档 → 纠正 → 写回

# 高精度（small 模型 + 领域文档纠正）
python subtitle_pipeline.py "./videos/" --model small
# Claude: 读取输出 → 用户提供 "操作手册.docx" → 结合纠正 → 写回

# 英文视频
python subtitle_pipeline.py "./videos/" --language en --no-simplify
```

## 常见问题

| 问题 | 解决 |
|------|------|
| SSL 证书错误 | 脚本已内置 certifi 修复 |
| HuggingFace 下载慢 | 已配置 hf-mirror.com 镜像 |
| 转录不准确 | 换 `--model small` 或 `--model medium` |
| GBK 终端乱码 | 文件本身是 UTF-8，直接 Read 工具读取 |
| 模型已下载仍报错 | 检查 `<skill_dir>/.whisper_models/` 目录完整性 |
