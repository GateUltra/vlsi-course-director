# VLSI Course Director · 课程制作技能库

[English](README.md) · [完整复现命令](vlsi-html-course-studio/references/reproduce-v2.md) · [下载当前技能包](downloads/vlsi-html-course-studio-skill.zip)

本仓库将制作课程视频、交互网页、配音字幕和习题的方法，落实为可运行的制作工具与课程包接口。它是公开的技能源码仓库，不是课程网站。

## 三个入口

- **[HTML Course Studio 2](vlsi-html-course-studio/SKILL.md)**：当前推荐入口，共用制作内核、替换课程包、完整有声样例与自动校验。
- **[原始 Course Director](vlsi-course-director/SKILL.md)**：保留轻量导演流程，技术路线灵活。
- **[HTML Studio v1 压缩包](downloads/vlsi-html-course-studio-v1.0.0.zip)**：保留上一版方法、无声模板和 Placement 源码先例，可回滚使用。

## 新版怎样复用

课程包保存知识模型、SVG 图板、动作、教学意图、台词、译文、音色设置、点评和习题。播放器、配音编排、实测时钟、逐帧导出和完整性验证由同一内核执行。

现成的两套短样例分别讲两引脚线长、逻辑门延迟与关键路径；两者知识结构不同，共用同一内核。各自包含三幕、英中真实旁白缓存、独立字幕、可操作实验与允许多个答案的练习。第一次复现可以完全不调用在线 TTS。

新版检查文稿、声音、时钟、画面与字幕的版本依赖，拒绝新增片段却沿用旧声音、未知场景、损坏缓存和被改动的产物。构建失败不会留下冒充成品的最终目录。

## 安装与使用

在支持内置技能安装器的 Codex 对话里发送：

```text
$skill-installer install https://github.com/GateUltra/vlsi-course-director/tree/main/vlsi-html-course-studio
```

也可以复制整个文件夹到项目 `.agents/skills/`。已有同名安装先检查自己的修改。旧技能名称及路径保持不变。

```text
使用 $vlsi-html-course-studio，依据这些课程材料创建新的课程包：<链接或文件>。
面向首次学习的大学生，先交付真实配音样片、准确场景移交和一道可操作习题。
保留共用内核，独立验证知识模型，并报告实际执行的复现检查。
```

从零搭环境和构建两个样例，见[复现指南](vlsi-html-course-studio/references/reproduce-v2.md)。新增课程接口见[契约](vlsi-html-course-studio/references/course-pack-contract.md)。

## 能力边界与证据

当前内核支持确定性的 2D SVG、JSON 状态、数值/指针交互和按状态评分。它没有承诺自动生成任意风格或任意交互。小型样例证明工程链路；完整课程的研究、自然配音、翻译和视觉质量仍需审查。

原 39 幕 Placement 源码、人物 IK 和精细调优完整留底，尚未声称全部转为 v2 课程包。原有 123 个源码/工具文件有哈希基线；原版导演技能保持原样。

查看[本次验收记录](docs/HTML_STUDIO_V2_VALIDATION.md)和[迁移/回滚规则](vlsi-html-course-studio/references/migration-v2.md)。历史验收不冒充新课的通过记录。配音缓存支持离线复现，在线重合成的音色与时长仍可能随服务变化。
