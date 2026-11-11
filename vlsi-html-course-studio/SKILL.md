---
name: vlsi-html-course-studio
description: Design and produce VLSI or EDA courses with shared HTML/SVG video animation, multilingual narration and captions, interactive labs, a teaching companion, and exercises. Use for creating or substantially revising this integrated learning experience, especially when movie scenes must transfer into a live lab; not for an isolated EDA answer or a generic website.
---

# VLSI HTML Course Studio

担任课程导演与实现者，把教学目标落实为可播放的视频、可操作的网页、可解释的习题反馈和可继续编辑的源文件。以用户当前任务为范围；规划、样片、完整制作、修改、发布是不同工作，不自动扩展到其他阶段。

这是从完成的 Placement Lesson 06 提炼的方法包。**复用架构与验证方法，重新设计下一课的知识模型与叙事。** 示例中的容量、坐标、章节、人物、音色、时长都不是新课程的固定要求。

## 开始工作

1. 先读项目现有入口、课程原文、作业要求和用户已认可的样片。定位真实课号、仓库路径和版本；不要凭目录编号推断课程。按 [课程研究与导演](references/research-direction.md) 确定受众、学习目标和可动画化的因果关系。
2. 建立可独立验证的领域模型，再写故事。分别标记原课算法、为讲解设计的例子、示意动画和真实求解结果。原始实验如果不能达到理想目标，应解释约束而非改造结果让故事“成功”。
3. 新课制作通常先做 45–60 秒真实样片，包含核心解释、实际配音、代表性动画、场景转入实验和有意义的反馈。用户已认可方向或直接授权完整制作时继续推进；本 skill 不额外要求确认。
4. 只读当前阶段需要的参考资料；不要为一次小修改载入整个实例。

未指定时，可把“首次学习该课的大学生、英文教学画面、用户语言沟通”作为工作假设。明亮科学家工作室是经过验证的可选方案，不能覆盖用户指定的风格或受众。

## 工作流与资料入口

| 当前工作 | 先读 | 可用实现 |
|---|---|---|
| 研究课程、脚本、样片节奏 | [课程研究与导演](references/research-direction.md) | `assets/planning/lesson-brief.md`、`cue-sheet.json` |
| 视频、实验、习题共用状态 | [共享架构与数据契约](references/shared-architecture.md) | `assets/starter/`、[起步模板](references/starter.md) |
| 科学家动作与实验点评 | [角色与点评](references/character-mentor.md) | 实例的 `scientist-rig.js`、`mentor.js` |
| 配音、BGM、字幕和多语时序 | [音频与字幕](references/audio-captions.md) | 实例的 `scripts/make_course_audio.py` |
| HTML 渲染、语义片段变速、媒体检查 | [制作工具](references/tooling.md) | `scripts/render_html.py`、`retime_video.py`、`validate_media.py` |
| 播放器、练习、验收、交付 | [网页与验收](references/site-verification.md) | 实例的 `player.js`、`exercises.js`、浏览器检查脚本 |
| 修改后重建范围、分工 | [修改与协作](references/change-and-coordination.md) | 内容→音频→时钟→画面→字幕→网页依赖 |
| 查看完整已实现先例 | [Placement 实例](references/placement-case-study.md) | `assets/placement-lesson06-source/`，仅源码，不含成片 |

## 保持这些实现约束

- **一个知识模型。** 领域规则、评分、角色点评和画面数字都调用同一组纯函数；验证用独立计算或原课参考实现，不能只让实现自证。
- **一个语义状态。** 稳定 `cueId`、每音色实测时钟、纯函数 `stateAt(t, clock, script)`、可随机访问的 `renderAt(t)`。不要依赖“先播放过哪些帧”得到当前画面。
- **同组件，不同交互外壳。** 视频时间轴驱动状态，实验由用户驱动。转入实验复制准确坐标、约束、模式与参数，包括正在运动的中间帧。
- **语音决定时长。** 每种配音单独测量，画面按语义片段匹配；不要用整段速度比例假定每句等长。只有纯视觉、归一化进度驱动的片段才适合复用变速。口型、拍点或逐字动作需要重新渲染或细化时标。
- **字幕与配音独立。** 保存“音色 × 字幕语言”的时间表，允许关闭字幕。小屏可把字幕放到画面下方；原生视频全屏用 native track。技术检查与母语审校分别报告。
- **反馈有依据。** 角色说“改善”“仍拥挤”“建议移动”前先计算现状态、前状态或候选状态。区分可行性、目标改善和全局最优。
- **来源与产物可追溯。** 记录课件版本、素材许可证据、TTS 服务音色、缓存键、实测时长、生成命令和已执行检查。上次项目的在线服务授权不是未来所有项目的通行证；按当前授权范围工作，不重复询问已获授权事项。
- **交付与发布分开。** 本地网站包含真实媒体、相对路径、启动方式和源文件说明。源码模板不能当成已完成视频；没有公开 URL 实际验证就不声称上线。

## 快速起步

以下 `<skill>` 指本文件所在目录。目标目录必须不存在，避免覆盖已有课程。

```powershell
python <skill>/scripts/init_course.py --destination ./new-vlsi-lesson --title "A new VLSI lesson"
python <skill>/scripts/serve_site.py --directory ./new-vlsi-lesson --port 8780
```

打开 `http://127.0.0.1:8780/`。模板是**无配音的交互分镜演示**，验证共用组件、时间轴、实验移交和评分，不包含真实课程成片或在线 TTS 调用。按 [起步模板](references/starter.md) 替换领域模型和内容，再进入真实音频与渲染流程。

Placement 源码快照用于查阅复杂组件。其课程专用生产脚本保留原配置，移植前需修改 URL、浏览器路径、课程模型等；通用工具位于本 skill 的 `scripts/`。依赖与命令见 [制作工具](references/tooling.md)。

## 完成的证据

先验证知识，再检查代表性静帧与实际音频，最后验证完整影片和真实浏览器交互。执行与改动相关的检查；无需因文案微调重新跑无关大规模渲染。记录通过项、未检项和限制，给用户可打开的成品与编辑入口。详见 [网页与验收](references/site-verification.md)。
