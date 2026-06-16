# HyperFrames 拼接

## 输入
- `output/composition_manifest.yaml`
- `output/videos/SXX_clip.mp4`
- `output/audio/audio_manifest.yaml`
- `output/shots/SXX.md`

## 任务
1. 按分镜顺序拼接视频。
2. 在片段边界应用合适转场。
3. 按时间轴叠加字幕。
4. 预留或接入音频轨。
5. 输出最终成片。

## 合成清单应包含
```yaml
timeline:
  - shot_id: S01
    clip_path: output/videos/S01_clip.mp4
    transition_out: dissolve
    subtitle_track: true
    audio_track: reserved
```

## 转场规则
- 只在分镜边界做转场。
- 转场类型由前后分镜的情绪与构图关系决定。
- 同一项目尽量保持转场体系统一，不要每个镜头都换一种。

## 输出
- `output/final.mp4`
- 保留全部中间片段
- 保留合成清单和字幕信息

## 失败回退
如果 HyperFrames 不可用：
- 保留全部分镜视频和清单
- 提供手动剪辑所需的顺序与转场建议
- 不删除任何生成结果
