# 单分镜文档结构

## 文件
每个分镜保存为：
`output/shots/SXX.md`

## 推荐结构
每个分镜文档使用 Markdown，顶部保留 YAML frontmatter：

    ---
    shot_id: S01
    sequence_index: 1
    title: ""
    duration_seconds: 8
    start_timecode: "00:00"
    end_timecode: "00:08"
    narrative_role: ""
    ---

正文包含以下固定章节：

- `## 元数据`
- `## Prompt Brief`
- `## Image Prompt`
- `## Video Prompt`
- `## Negative Prompt`

元数据建议：

    transition:
      from_previous: ""
      to_next: ""
      suggested_transition: ""

    subtitle:
      enabled: true
      text: ""
      start_offset_seconds: 1.0
      duration_seconds: 4.0
      position: bottom_center

    audio:
      required: true
      status: reserved
      voiceover_text: ""
      placeholder_path: output/audio/S01_voiceover.mp3

Prompt Brief 建议：

    visual_goal: ""
    concrete_subjects:
      - ""
    scene_type: ""
    camera:
      shot_size: ""
      angle: ""
      lens: ""
    motion_intent: ""
    tone: ""
    must_avoid:
      - ""

## 字段要求
- `shot_id` 使用 `S01` 格式。
- `sequence_index` 从 1 连续递增。
- `duration_seconds` 不要超过当前视频工具稳定范围。
- `subtitle.enabled` 表示是否需要后期字幕。
- `audio.required` 表示是否需要生成或预留音频。
- `image_prompt` 不描述运动。
- `video_prompt` 不重新定义场景，只描述基于关键帧的运动。

## 禁止
- 不要把分镜说明写成唯一提示词。
- 不要在视频提示词里要求生成中文大字。
- 不要让一个分镜包含两个以上地点。
- 不要让单个视频提示词包含多个镜头切换。
