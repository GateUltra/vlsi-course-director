# Placement Lesson 06 — source-only worked example

本目录保存 2026-11-11 完成版本的源码和历史验证记录，供学习与改造。完整成片仍在原项目交付中。这里**没有四个 MP4、生产期 MP3/WAV 缓存、画面母版或 Python 依赖**，因此直接打开 `course/index.html` 会缺少视频；这不是一个已经打包好的完整网站。

需要可立即运行的最小例子时，使用本 skill 的 `assets/starter/` 和 `scripts/init_course.py`。需要查看本课完整角色、播放器、七语言字幕、实验与渲染方式时，阅读本快照。

## 保留内容

- `course/`：全部可编辑 HTML/CSS/JS、39 cue 文稿、翻译、术语、四套实测时钟、28 VTT、角色 SVG 和来源记录。
- `scripts/`：原课程音频生成、主图像渲染、语义重定时、打包和相关验收脚本。
- `review-course/`：当时针对**原完整项目**执行的检查报告；不是本快照或下一课再次执行的结果。
- `SNAPSHOT.json`：所复制文件的相对路径、大小和 SHA-256。文件内容保留原样，包括历史路径/命令/报告。

## 怎样复用

从 `course/domain.js → board.js → timeline.js → scene.js` 看数据怎样变成画面，再读 `player.js → lab.js → mentor.js → exercises.js` 看同一状态怎样变成学习操作。

重点可独立提取的模式：

- `scientist-rig.js` 的双骨 IK 与头像/全身模式；搭配 `scientist-art.js` 和素材来源。
- `player.js` 的语义音色切换与字幕下移/全屏行为；它依赖本例 DOM ID，不能当无配置组件直接插入任意站点。
- `make_course_audio.py` 的精确缓存、实测时钟、低音量原创配乐和数字安全字幕分段；替换课程文本、音色配置和路径，按当前项目授权调用在线服务。
- `render_course.py` 的主画面 + 逐 cue 变速；本 skill 通用脚本 `scripts/render_html.py` / `retime_video.py` 已将端口、浏览器、路径与音色参数化，更适合新项目。

原生产脚本保留 Windows Chrome 路径、8770 端口、`.pydeps` 和课程专用断言。它们是实际实现先例，**不是未配置就能运行的跨平台 SDK**。若需重建该课，先安装依赖并调整配置、提供生产音频或在有授权时重新生成，再渲染和验收。只想查看画面时，服务 `course/` 后的 `render.html` 可读取已保留时钟，不需要 MP4。

原 `course/README.md` 是当时完整交付的说明，其中媒体、生产目录与运行证据指向完整项目；阅读时以本文件说明的快照范围为准。原 `assets/rig-provenance.json` 含样片时期的声音驱动表情描述；完整版默认实际使用 cue 进度的表达性胡须微动，详见本 skill `references/character-mentor.md`，不代表音素同步。

另有两处保留的历史引用：`course/domain.js` 注释里的 `assets/course-sources.json` 未包含在完成版中，来源请查 `course/CREDITS.md`；原README提到的 `scripts/check_course_domain.mjs` 依赖未打包的归档上游代码，因此未纳入本轻量快照。不要把该命令缺失视为新课程的验证结果；可迁移的新模板有自己的 `check.mjs`。

## 来源与权利

请保留 `course/CREDITS.md` 和相关 provenance。角色头像的 CC0 记录与独立原创身体代码有明确说明；原课程 README 的许可意图没有被当成已验证的全仓库许可。历史数字与算法例子须重新核实适用性。分享改造品时按各来源的实际权利和授权处理，不因这些文件被放入 skill 就视为获得新的许可证。
