# 音频生成

## 工具
使用 `scripts/voicertool_tts.py` 生成 MP3 配音。脚本复用 Voicertool 页面公开使用的 Edge Read Aloud 语音服务：
- 默认语种：`zh-CN`
- 默认人物：`zh-CN-YunyangNeural`
- 默认输出：`output/audio/voiceover.mp3`
- 支持音调、速度、音量参数

## 常用命令
查看帮助：
```powershell
$env:PYTHONUTF8='1'; python scripts/voicertool_tts.py -h
```

生成默认中文配音：
```powershell
$env:PYTHONUTF8='1'; python scripts/voicertool_tts.py --text "让每一步流程清晰可控" --out output/audio/S03_voiceover.mp3
```

从 UTF-8 文本文件生成：
```powershell
$env:PYTHONUTF8='1'; python scripts/voicertool_tts.py --text-file output/audio/S03_voiceover.txt --out output/audio/S03_voiceover.mp3
```

调整声音参数：
```powershell
$env:PYTHONUTF8='1'; python scripts/voicertool_tts.py --text "让每一步流程清晰可控" --voice zh-CN-YunyangNeural --pitch "+0%" --rate "-5%" --volume "100%" --out output/audio/S03_voiceover.mp3
```

列出语种：
```powershell
$env:PYTHONUTF8='1'; python scripts/voicertool_tts.py --list-languages
```

列出中文人物：
```powershell
$env:PYTHONUTF8='1'; python scripts/voicertool_tts.py --list-voices --language zh-CN
```

## 参数
| 参数 | 默认值 | 说明 |
|---|---|---|
| `--text` | 无 | 直接输入文本 |
| `--text-file` | 无 | 从 UTF-8 文件读取文本 |
| `--out` | `output/audio/voiceover.mp3` | 输出 MP3 |
| `--language` | `zh-CN` | 语种/区域 |
| `--voice` | `zh-CN-YunyangNeural` | 人物 ShortName |
| `--pitch` | `0%` | 音调 |
| `--rate` | `0%` | 速度 |
| `--volume` | `100%` | 音量 |
| `--list-languages` | false | 展示可用语种 |
| `--list-voices` | false | 展示人物 |
| `--voice-query` | 无 | 过滤人物 |
| `--dry-run` | false | 打印请求，不生成 |

## 集成规则
- 如果分镜 `audio.required = true`，优先生成真实 MP3。
- 如果网络或服务不可用，保留占位，不阻断图片/视频生成。
- 生成的 MP3 路径写回 `audio.placeholder_path` 对应字段。
- 不把字幕轨和音频文件混用。
- Windows 下必须在 Python 启动前设置 `PYTHONUTF8=1`，否则中文 `--text` 可能被系统编码解码成乱码。长文本优先使用 `--text-file`。
