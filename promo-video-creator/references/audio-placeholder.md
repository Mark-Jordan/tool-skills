# 音频占位

## 当前状态
本 skill 已支持通过 `scripts/voicertool_tts.py` 生成 MP3。若网络或服务不可用，则保留占位结构，不阻断视频生成。

## 触发条件
只要分镜满足以下任一条件，就生成 MP3 或创建音频占位：
- `audio.required = true`
- 该镜头包含旁白语义

仅有后期字幕、没有旁白语义时，不生成音频。

## 需要保留的字段
```yaml
shot_id: S03
required: true
voiceover_text: "让每一步流程清晰可控"
placeholder_path: output/audio/S03_voiceover.mp3
status: reserved
```

## 规则
- 不删除占位文件。
- 不把字幕文件当成音频文件。
- 真实生成规则见 `references/audio-generation.md`。
- 若该镜头无文字，则 `required: false`，但仍可保留空占位记录。
