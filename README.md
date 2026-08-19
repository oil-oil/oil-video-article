# oil-video-article

![banner](assets/banner.svg)

把一期视频变成一篇公众号 Markdown 文章。这是一个 agent skill（Claude Code / Codex / DeepSeek Harness 等支持 SKILL.md 的 agent 都可以加载）：读字幕理解视频，截取真实画面当配图，逐张核对后按文章结构成稿。只生成文章和图片，不发布。

## 两种输入

- **Screen Studio 工程**：配图从没有头像、没有缩放包装的纯屏幕录制轨道（`channel-*-display-*.mp4`）截取，时间轴经 `project.json` 的 slices 映射回 source 时间，支持导出后又有剪辑的错位校正。
- **普通视频**（mp4/mov）：字幕时间就是视频时间，直接从视频本身截帧。

两种输入都需要字幕语料（`.srt` / `.ass`）。没有字幕时先用 [oil-subtitle](https://github.com/oil-oil/oil-subtitle) 生成。

## 安装

```bash
git clone https://github.com/oil-oil/oil-video-article ~/.agents/skills/oil-video-article
```

`~/.claude/skills/`、`~/.codex/skills/` 等你的 agent 实际扫描的 skill 目录也可以。

依赖：`python3`、`ffmpeg` / `ffprobe`。

## 使用

把工程目录或视频文件连同字幕交给 agent 即可，例如：

> 把 `~/Movies/视频项目/2026-08-13_示例/` 这一期整理成公众号文章。

agent 会按 `SKILL.md` 的流程执行：读字幕分段 → （工程模式）检查时间轴一致性 → 截配图 → 逐张核对 → 补全可复制的原始命令和链接 → 按 [oil-tone](https://github.com/oil-oil/oil-tone) 的规则成稿 → 输出到 `<视频目录>/公众号文章/`。

## 配套

- [oil-subtitle](https://github.com/oil-oil/oil-subtitle)：转录和字幕烧录，提供本 skill 的字幕语料。
- [oil-tone](https://github.com/oil-oil/oil-tone)：成稿文风规范和 lint。
- [screen-studio-editor](https://github.com/oil-oil/screen-studio-editor)：上游剪辑。
- [dsh-oil-creator](https://github.com/oil-oil/dsh-oil-creator)：DeepSeek Harness 内容工作台，展示本 skill 的产出。

## License

[MIT](LICENSE)
