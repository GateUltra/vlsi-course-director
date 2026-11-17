---
name: vlsi-html-course-studio
description: Create or revise VLSI/EDA lessons whose narrated HTML/SVG animations, interactive labs and exercises must share a verified model. Use for integrated course production or reproducible course-pack migration, not isolated EDA answers, ordinary websites, or a promise to automate every visual style.
---

# VLSI HTML Course Studio 2

把教学意图变成可验证的模型、影片、实验和习题。按用户要求处理规划、样片、完整制作或修改，不因加载本 skill 自动扩大范围。与用户使用其语言；教学界面语言由任务决定。

**先分清任务。** 新建可复现课程使用下面的 v2 课程包流程；维护已有 Placement 或其他实现时保留其接口与精度，不为符合模板强行迁移。v1 无声 starter、六个工具及完整 Placement 源码快照保留为基线，不能当作 v2 完整生产入口。

## 支持范围与边界

v2 内核支持确定性的 2D SVG 图形、可序列化模型状态、数值控制或归一化指针操作、按状态评分的练习，以及多音色视频和独立字幕。课程专属模型、画板、动作、规则、测试及素材都属于课程包，允许包含代码。3D、开放式在线问答、音素口型或特殊交互需要另行设计；不要暗改共享内核来伪装成已经支持。

浏览成品不需要 Python、Node 或 TTS 服务，这些仅用于制作。固定音频 fixture 可离线复现；在线重新合成依赖服务且声波可能变化，不能承诺逐字节重现。

## 导演与制作

1. 读取真实课程、作业和现有成果，记录来源版本、受众、目标与简化边界。用独立期望值核对模型。见 [课程研究](references/research-direction.md)。
2. 以 `lesson.json` 的 cue 定义目标、旁白、字幕、场景引用和练习关联；这是本次课程的共享意图。一个 cue 是一个可独立计时的解释，不按任意秒数切分。画面解释的数值来自模型，不能手写一套不同答案。
3. 实现或替换**一个课程包**，遵循 [课程包契约](references/course-pack-contract.md)。不得让通用播放器、配音器或渲染器认识 A/B 引脚、某条路径或特定题目。先跑模型和接入检查，再生成声音。
4. 制作有真实讲解、核心变化、场景移交与反馈的代表性样片。通常 45–60 秒；本包的短基准用于验工程，不能代替完整课程的教学设计。已获授权的阶段直接推进。
5. 经当前任务授权使用 TTS，或读取有来源和精确指纹的固定音频。每音色逐 cue 实测时长，派生时钟、字幕、章节和画面；正式构建拒绝旧文稿配旧声音、缺 cue、未知场景和临时时钟。生成命令和环境必须记录。
6. 让学生把正在观看的准确状态带入实验，保留中间帧与模型参数。点评计算实际变化，题目按约束接受不同正确答案。保留当前音色的语义位置、字幕、倍速与暂停状态。
7. 执行部件检查、跨产物一致性检查和真实浏览器验收，再查看代表性画面与实际声音。自动测试证明结构与数值；自然配音、翻译、节奏和教学清晰度需另行审查并注明范围。

## 可执行入口

从 skill 所在目录，按 [复现指南](references/reproduce-v2.md) 建立隔离环境，再执行：

```powershell
.\.venv\Scripts\python.exe scripts/studio.py doctor
.\.venv\Scripts\python.exe scripts/studio.py check --course assets/course-packs/wirelength --audio-mode fixture
.\.venv\Scripts\python.exe scripts/studio.py build --course assets/course-packs/wirelength --out ./wirelength-site --audio-mode fixture
.\.venv\Scripts\python.exe scripts/studio.py verify --site ./wirelength-site
.\.venv\Scripts\python.exe scripts/serve_studio.py --directory ./wirelength-site --port 8780
```

输出目录必须不存在；失败不会留下冒充成品的最终目录。先运行 `--help` 了解可用参数。课程包的 `check.mjs` 是独立知识期望；共用检查负责接口、状态、时序、媒体和版本依赖。

另一个结构不同的包是 `assets/course-packs/logic-timing/`。迁移时把它替换为自己的包，保持 `assets/runtime/` 与生产工具不变。修改原包文稿后，不能沿用其音频 fixture；使用明确的在线命令重新生成并核验新缓存。

## 按需读取

| 工作 | 资料 |
|---|---|
| 首次复现、环境和命令 | [复现与验收](references/reproduce-v2.md) |
| 新课程接入、状态、意图与版本 | [可执行契约](references/course-pack-contract.md) |
| 修改、兼容、基线和发布 | [迁移与演化](references/migration-v2.md) |
| 叙事与精确移交的设计依据 | [课程研究](references/research-direction.md)、[共享架构](references/shared-architecture.md) |
| 角色、IK动作、指标点评 | [角色与点评](references/character-mentor.md) |
| 配音选择、字幕断句、BGM、审听 | [音频与字幕](references/audio-captions.md) |
| 教学网站完整性 | [网页验收](references/site-verification.md) |
| 细节先例与原参数 | [Placement 实例](references/placement-case-study.md)、源码快照 |

不一次读完所有参考，不按流程机械拆成多个 skill。多智能体协作时，导演维护同一课程包意图与接口版本，分工围绕独立产物验收，冲突先回到意图层处理。

## 发布判据

新实现先作为候选，使用保留基线做回归；新增课程在声明能力内只能改课程包。至少用不同知识结构的课程做独立试用，记录是否修改了内核、是否需要额外口头帮助。报告区分本次执行与历史结果、工具链正确与教学质量。

交付可打开的网站、真实媒体、源文件和准确复现命令。发布依用户当前授权与指定仓库；没有远端提交或网页实际证据，不声称已发布。旧版、基线和回滚入口保留。
