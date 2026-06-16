# 音频占位

## 当前状态
本 skill 只预留音频结构，不负责真实音频生成。

## 触发条件
只要分镜满足以下任一条件，就创建音频占位：
- `subtitle.enabled = true`
- `audio.required = true`
- 该镜头包含旁白语义

## 需要保留的字段
```yaml
shot_id: S03
required: true
voiceover_text: "让每一步流程清晰可控"
placeholder_path: output/audio/S03_voiceover.wav
status: reserved
```

## 规则
- 不删除占位文件。
- 不把字幕文件当成音频文件。
- 后续补全 TTS 或配音能力时，只替换实现，不改协议。
- 若该镜头无文字，则 `required: false`，但仍可保留空占位记录。
