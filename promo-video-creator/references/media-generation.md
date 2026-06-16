# 图片与视频生成

## 原则
- 先关键帧，后视频。
- 先通过 prompt brief，再调用生成。
- 长提示词优先使用 `--prompt-file`。
- Windows 命令统一加 `PYTHONUTF8=1`。

## 图片生成
1. 读取 `output/shots/SXX.md`
2. 提取 `image_prompt`
3. 必要时并行生成 2-3 个版本
4. 输出到 `output/images/SXX_keyframe.png`
5. 检查文件存在且可用

推荐命令：
```powershell
PYTHONUTF8=1 python scripts/agnes_api.py image --prompt-file prompt.txt --size 1280x720 --out output/images/S01_keyframe.png
```

## 视频生成
1. 读取同一分镜文档
2. 确认关键帧已存在
3. 提取 `video_prompt`
4. 使用关键帧 + 视频提示词生成 clip
5. 输出到 `output/videos/SXX_clip.mp4`

推荐命令：
```powershell
PYTHONUTF8=1 python scripts/agnes_api.py video --prompt-file video_prompt.txt --image output/images/S01_keyframe.png --seconds 8 --out output/videos/S01_clip.mp4
```

## 批量执行
- 以 3-5 个分镜为一组并行处理。
- 先全部生成关键帧，再进入视频生成。
- 每组结束后做一次人工或半自动质量检查。

## 生成约束
- 视频提示词必须和关键帧一致。
- 不在提示词里要求模型直接输出字幕文字。
- 需要字幕时，在分镜文档中记录字幕信息，交给后期轨道。
- 需要旁白时，只预留音频占位，不在本阶段补音频。

## 失败处理
- 关键帧偏离预期：重写 `prompt_brief` 后再生成。
- 视频跑偏：优先收紧 motion_intent 和 must_avoid。
- 出现乱码：检查 `PYTHONUTF8=1` 和 `--prompt-file`。
