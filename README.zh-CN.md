# VLSI Course Director · 课程制作技能库

[English](README.md) · [新版详细用法](docs/HTML_STUDIO_GUIDE.md) · [下载新版技能包](downloads/vlsi-html-course-studio-skill.zip)

这个仓库分享实际制作 VLSI / EDA 课程时形成的方法：研究课程、设计叙事、制作动画和声音、准备字幕、实现交互网页与习题，并交付可编辑源码。它是社区技能库，不是课程网站，也不是 OpenAI 官方技能。

## 两个版本如何选择

| 版本 | 适合的任务 | 主要内容 |
|---|---|---|
| **[vlsi-html-course-studio](vlsi-html-course-studio/SKILL.md)** 新版 | 视频、网页、实验和题目共用 HTML/SVG 组件与状态；需要多语言和互动讲解角色 | 9份详细指南、6个工具、可运行分镜模板、Placement Lesson 06源码实例 |
| **[vlsi-course-director](vlsi-course-director/SKILL.md)** 原版 | 更轻量、技术路线灵活的课程导演流程 | 原有说明、课程蓝图、Floorplanning案例、本地服务与媒体验证 |

**旧版目录和安装路径原样保留。** 两个技能使用不同名称，可以并存，按任务明确调用。新版指南主要用中文撰写，代码及教学界面示例默认英文。

## 安装与调用

在支持内置技能安装器的 Codex 对话中发送（不是在 PowerShell 里执行）：

```text
$skill-installer install https://github.com/GateUltra/vlsi-course-director/tree/main/vlsi-html-course-studio
```

旧版仍可使用：

```text
$skill-installer install https://github.com/GateUltra/vlsi-course-director/tree/main/vlsi-course-director
```

手动安装时，克隆或下载仓库，把完整的目标技能文件夹复制到项目的 `.agents/skills/` 中，保留内部相对目录。已有同名版本先检查，避免覆盖自己的修改。如果新技能未显示，重启会话。安装位置和发现机制以 [官方说明](https://learn.chatgpt.com/docs/build-skills) 为准。

然后把课程材料交给 AI，例如：

```text
使用 $vlsi-html-course-studio 制作这节 VLSI 课程：<课程链接>。
面向第一次学习该主题的大学生，英文教学画面，与我用中文交流。
先制作45–60秒真实配音样片和共享组件的交互版本，
保留已约定的音色与视觉风格，设计一个预测问题和配套练习。
```

其他 AI 工具可以按其技能机制安装，或直接读取 `SKILL.md`。技能支持任务范围，不会因为读到制作指南就自动调用在线语音服务或发布网站。

## 新版包含的方法

- 课程原文、作业、算法与数值核验；面向大学初学者的因果叙事。
- HTML/CSS/SVG构图、确定性随机访问渲染、视频/实验/习题共用模型。
- 科学家闭嘴与胡须微动、双骨IK手势、头像/全身切换、基于真实指标的点评。
- 实测每种配音的时间轴、精确缓存、语义片段重定时、低音量BGM。
- 配音和字幕独立选择、英中法西德日韩字幕、小数安全断句、全屏字幕处理。
- 章节跳转、倍速、语义位置切换、视频中间状态移交、键盘/触摸操作与多解习题。
- 逐层验收、修改后的重建范围、多智能体分工和完整源文件交付。

## 无需在线服务即可试用

在仓库根目录执行，要求 Python 3.10+，目标目录必须尚不存在：

```powershell
python vlsi-html-course-studio/scripts/init_course.py --destination ../my-vlsi-lesson --title "My VLSI Studio"
python vlsi-html-course-studio/scripts/serve_site.py --directory ../my-vlsi-lesson --port 8780
```

打开 `http://127.0.0.1:8780/`。模板是明确标注的 **32秒无声分镜**，可以拖动点、用键盘微调、把当前画面带进实验并完成一道多解练习。它用来验证技术结构，不冒充带配音成片。

正式制作需要课程模型、真实旁白、实测时钟与字幕；渲染另需 Playwright/Chromium和FFmpeg。详细命令见 [制作工具说明](vlsi-html-course-studio/references/tooling.md)，实际验证见 [验证记录](docs/HTML_STUDIO_VALIDATION.md)。

Placement案例提供完整可读源码和历史记录，**不含MP4、原始音频或依赖环境**；直接打开案例网页会缺少视频。请先读 [源码快照说明](vlsi-html-course-studio/assets/placement-lesson06-source/SNAPSHOT_README.md)。

## 授权和来源

原创技能说明、通用工具及原创起步模板遵循仓库 [MIT License](LICENSE)。第三方头像采用CC0来源记录；课程来源和改写实例另有说明，不因为被放进技能库就改变其权利状态。详见 [第三方来源说明](THIRD_PARTY_NOTICES.md) 和案例 [CREDITS.md](vlsi-html-course-studio/assets/placement-lesson06-source/course/CREDITS.md)。
