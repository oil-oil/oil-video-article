---
name: oil-video-article
description: 视频转公众号图文工作流。将 Screen Studio 工程或普通视频（mp4/mov）配套字幕整理为本地公众号 Markdown 文章，截取真实画面、逐张核对并按文章需要插入配图；默认搭配 oil-tone，只生成文章和图片，不发布。用户提到“把视频整理成文章 / 公众号文章 / 图文稿 / 推文”、要求补视频文章配图，或提供 Screen Studio 工程、普通视频加字幕时必须使用。
---

# oil-video-article

把一期视频变成一篇 oil 口吻的公众号文章。支持两种输入：

- **Screen Studio 工程**：配图从**没有头像的纯屏幕录制轨道**（文件名含 `display`）里截取，而不是从带头像的导出成片里截图。不同 Screen Studio 版本可能使用 `channel-1-display` 或 `channel-2-display`，不要写死通道编号。
- **普通视频文件**（mp4/mov）：没有独立屏幕轨道，配图直接从视频本身截取，画面带摄像头头像或包装是正常的，选帧时优先挑屏幕内容占主体的时刻。

两种输入都必须有字幕语料（`*_subtitled.ass` 或 `.srt`）：没有字幕先让用户跑 oil-subtitle 生成，不要靠猜画面写文章。

## 输入

向用户确认两样东西（通常用户会直接给出）：

- 视频来源：`.screenstudio` 工程目录，例如 `~/Screen Studio Projects/Area XXXX.screenstudio`；或普通视频文件，例如 `~/Movies/视频项目/<视频标题>/<标题>.mp4`
- 字幕文件（`*_subtitled.ass` 或 `.srt`），通常在 `~/Movies/视频项目/<视频标题>/` 下

字幕时间是选配图时间点的唯一依据。Screen Studio 工程中字幕对应 edited 时间轴；普通视频中字幕时间就是视频时间，两者是同一根时间轴。

每次开始先设置：

```bash
SKILL_DIR="$HOME/.agents/skills/oil-video-article"  # 按实际安装位置调整
```

## 流程

### 1. 读字幕，理解视频

通读 ass/srt（ass 里只取 `CaptionText` 行的文本和时间），把视频分成几个内容段落，记下每个段落的关键时间点。

### 2. 检查时间轴一致性（仅 Screen Studio 工程，不能跳过）

普通视频没有这一步：字幕和视频是同一根时间轴，直接进入第 3 步。

Screen Studio 工程里，字幕对应的是**导出时**的 edited 时间轴；`project.json` 可能在导出之后又被保存/剪辑过，两者会错位。

```bash
python3 "$SKILL_DIR/scripts/extract_frame.py" --project "<工程>" --list   # 看 slices 总时长
ffprobe -v error -show_entries format=duration -of csv=p=0 "<导出视频.mp4>"
```

- 两者一致（差 < 1s）：直接用字幕时间截帧。
- 不一致：定位导出后发生的剪辑点。方法：在视频前、中、后各取 2-3 个时间点，分别从导出视频和映射后的 display 轨道截小图（scale=640），用 ReadMediaFile 逐对对比，找到开始错位的位置 C 和总差值 D。字幕时间 t < C 直接用 t，t ≥ C+D 用 t - D。找不到可靠规律时，逐个用画面内容反推，不允许凭猜测截帧。

### 3. 截配图

根据文章结构和信息密度按需挑选配图时刻，不预设图片数量。每张图都应承担说明步骤、展示结果、呈现对比或提供事实证据的作用；没有新增信息时不为了凑数量重复配图。优先选择「操作结果已经稳定显示」的瞬间（通常比字幕提到该动作的时间晚 1-3 秒）。

Screen Studio 工程（第 2 步校正后的 edited 秒）：

```bash
python3 "$SKILL_DIR/scripts/extract_frame.py" \
  --project "<工程>.screenstudio" \
  --time <edited 秒，按第 2 步校正> \
  --output /tmp/frame.png
```

脚本内部把 edited 时间经 `project.json` 的 `scenes[].slices[]` 映射回 source 时间，再从 `recording/channel-*-display-<session>.mp4` 截帧——这条轨道没有摄像头头像，也没有 Screen Studio 的缩放和背景包装。

普通视频（字幕时间直接用）：

```bash
python3 "$SKILL_DIR/scripts/extract_frame.py" \
  --video "<视频>.mp4" \
  --time <字幕秒> \
  --output /tmp/frame.png
```

两种模式截出的临时帧都转成 jpg 再进文章目录：

```bash
ffmpeg -hide_banner -loglevel error -i /tmp/frame.png -q:v 3 -y "<输出目录>/images/NN_名称.jpg"
```

### 4. 逐张核对（强制）

每一张图都必须用 ReadMediaFile 打开核对：

- 画面内容是否就是文章对应段落讲的那一步；
- 关键 UI（按钮、弹窗、终端输出、识别结果）是否完整清晰；
- 是否有加载中的空白页、无关的 toast、悬停菜单遮挡——有就前后移动 1-2 秒重截；
- 普通视频截图还要确认头像或包装没有挡住正文信息，挡了就换相邻时刻。

### 5. 补充可复制的原始内容

视频口播里被一句话概括、但读者需要复制使用的内容——命令、脚本、配置片段、安装语句、链接——必须从原始来源补全，不能以口播概括代替。视频里出现的文档页面 URL 可以直接从配图或字幕里确认。

用 `/ego-browser` 打开原始文档页面，抓取正文（`js()` 取 `main` 的 `innerText` 即可），核对内容后把原文的命令或配置以代码块形式插进文章对应段落，例如一键脚本、PowerShell 命令、安装语句。补充的内容必须是页面上真实存在的原文，不允许凭记忆或猜测补写命令。文章仍按视频主线组织，只补充视频实际讲到的那几处，不要把整篇文档搬进文章。

### 6. 写文章

调用 oil-tone skill，按它的规则成稿。由 `wechat-publisher` 调用时，还要完整读取并遵循它的 `references/article-writing-rules.md`。

成稿是文章，不是口播转写、功能清单或逐图说明。动笔前先在内部明确读者承诺、中心问题、一句话主线和 3–5 个关键节点。功能和截图只用于支撑这些节点；如果提纲只是按视频中的模块顺序逐项介绍，需要先重组。

文章要比口播稿更通顺、更完整。操作步骤用有序列表，并列的能力、厂商、区别用无序列表，列表项必须属于同一层级，剩下的连贯叙述保留自然段。

- 事实只能来自字幕、截图画面和第 5 步抓取的原始文档，不编造价格、参数、体验；
- 公众号语境：自然口语节奏，自己的操作用「我」，面向读者用「大家」；
- 标题朴素，小标题数量服从内容；叙事型或项目分享型文章可以不用小标题，也可以使用 2–4 个，教程和方法文章通常使用 3–6 个；图片用相对路径 `images/xx.jpg` 插在对应段落后面；
- 删除全部图片和小标题后，正文仍应具有连续的起因、推进和结果；
- 结尾说完就停，不加感悟和升华；
- 写完运行 `python3 "$HOME/.claude/skills/oil-tone/scripts/tone_lint.py" <成稿路径>`，通过后再人工通读一遍。

### 7. 输出位置

在视频目录下建 `公众号文章/`：

```
<视频目录>/公众号文章/<文章标题>.md
<视频目录>/公众号文章/images/NN_名称.jpg
```

## 汇报

简短说明：文章路径、配图数量、输入是工程还是普通视频、时间轴是否发生过导出后剪辑（以及怎么校正的）、每张图核对时做过的取舍。不要在回复里复述脚本内部逻辑。

文章成稿后，如果用户要求发布公众号或视频号，转 `oil-mp-publisher`（公众号图文排版+草稿）和 `video-publisher`（视频号）。
