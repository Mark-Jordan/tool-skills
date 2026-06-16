# 输出协议

## 目录
- 1. 总体目录
- 2. 分镜总览
- 3. 单镜头文档
- 4. 音频占位
- 5. 合成清单
- 6. 命名规则

## 总体目录
```text
output/
├── analysis_summary.md
├── storyboard_overview.md
├── composition_manifest.yaml
├── audio/
│   ├── audio_manifest.yaml
│   └── S01_voiceover.wav
├── images/
│   └── S01_keyframe.png
├── videos/
│   └── S01_clip.mp4
└── shots/
    └── S01.md
```

## 分镜总览
`storyboard_overview.md` 用于确定全片结构，建议包含：
- 项目目标
- 目标时长
- 分镜数量
- 每镜时长
- 位序与衔接关系
- 字幕分布策略
- 音频需求

建议字段：
```yaml
runtime_seconds: 180
shot_count: 15
shots:
  - shot_id: S01
    duration_seconds: 10
    role: opening
```

## 单镜头文档
每个 `output/shots/SXX.md` 必须包含：
- `shot_id`
- `sequence_index`
- `duration_seconds`
- `start_timecode`
- `end_timecode`
- `role`
- `transition_from_previous`
- `transition_to_next`
- `subtitle.enabled`
- `subtitle.text`
- `audio.required`
- `audio.placeholder_path`
- `prompt_brief`
- `image_prompt`
- `video_prompt`
- `negative_prompt`

## 音频占位
如果该镜头需要旁白或字幕语义绑定，则保留：
- `output/audio/audio_manifest.yaml`
- `output/audio/SXX_voiceover.wav`

当前 skill 只预留结构，不生成真实音频。

## 合成清单
`composition_manifest.yaml` 用于 HyperFrames 拼接，建议字段：
```yaml
timeline:
  - shot_id: S01
    clip_path: output/videos/S01_clip.mp4
    transition_out: dissolve
    subtitle_track: true
```

## 命名规则
- 使用稳定的 ASCII 文件名。
- 分镜编号固定两位数，例如 `S01`。
- 图像统一命名为 `SXX_keyframe.png`。
- 视频统一命名为 `SXX_clip.mp4`。
- 避免中文文件名进入自动化路径。
