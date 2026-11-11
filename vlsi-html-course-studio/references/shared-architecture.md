# 共享架构与数据契约

适用：开始新课，或让视频、交互与习题保持一致。以下契约是一种已验证的实现选择，不要求把现有项目迁移到同名文件。

## 六层职责

```text
source evidence → domain.js → verified examples / algorithm trace
                                  ↓
script cue IDs + measured clock → timeline.stateAt(t)
                                  ↓
                 Board(state) + Scene(state) + Character(pose)
                        ↙                    ↘
               Chromium → MP4          live experiment
                                            ↓
                              mentor(metrics) + grade(state)
```

- `domain.js`：坐标、网表、目标函数、约束、一步算法、完整轨迹。无 DOM、音频或随机鼓励。
- `board.js`：把状态画出来。固定 SVG `viewBox`、响应式尺寸；世界坐标和屏幕坐标转换集中定义。
- `timeline.js`：从时间确定状态、动画进度、标注与角色目标；不复制评分公式。
- `scene.js`：将图板、文字、公式、角色组成画面。网页版用 HTML 包住同一个 SVG 图板。
- `lab.js`：接收状态，处理拖动、键盘、参数与算法步进；动作后重算指标。
- `mentor.js` / `exercises.js`：解释和评估状态，返回结构化反馈；不自行移动点或伪造改进。

小模型与点评可以完全本地运行，无须在线 LLM。用户需要开放问答时再另行设计服务。

## 画面技术怎么选

HTML/CSS 适合可修改的文字、排版、卡片和网页控制；SVG 适合有含义的图元、连接线、公式标注、可点选对象和矢量角色。这两者组成这一案例的主要画面，不需要每帧用 Pillow 重画所有文字。

粒子或密集连线数量很大时，可让 Canvas 负责高频绘制，保留 HTML 的标签与无障碍说明；只有空间关系确实需要三维时再选择 WebGL。三种渲染技术都接受同一状态，不应因此各写一套知识模型。

位图仍适合照片、纹理、复杂插画和预渲染背景；可把它作为可替换资产嵌入 HTML/SVG。需要离线图像预处理时可以使用相应工具，但它不必成为整个动画的逐帧主绘图器。记录图像授权和源尺寸，避免导出1080p才发现角色糊掉。

视觉复杂度分配给需要强调的瞬间：片头、模型成形、关键反例、算法转折。解释公式时让眼睛有稳定落点。优先缓存不变的几何或复用SVG定义；确定性离线截图导出比实时屏幕录制更容易保证帧数和随机访问。帧率、分辨率和压缩参数先在小样本验证，30 fps是本案例选择，不是所有课程的固定要求。

## cue 是教学语义单位

cue 表达可独立计时的解释，如“建立包围盒”“读宽加高”，不按截图数量或任意5秒切句。稳定 ID 用于旁白、翻译、渲染、章节、回放、实验入口和增量构建。

```json
{"id":"measure_box","chapter":"03","title":"Measure the box",
 "layout":"measurement","en":"Add the width and height of this bounding box.",
 "zh":"把这个包围盒的宽和高相加。","pauseAfter":0.6}
```

一个 cue 内多个动作必须精确落在某词时，增加子标记或拆 cue。不要把“第一步/第二步/第三步”强压到一段线性进度；换语言后容易错位。翻译保持教学意图和数字，不强行保持英语语序。

## 每种配音一份实测时钟

```json
{"id":"en_gb","duration":12.4,"segments":[
 {"id":"measure_box","start":0.8,"end":5.1,"sceneEnd":5.7},
 {"id":"try_move","start":5.7,"end":11.2,"sceneEnd":11.6}
]}
```

`start` 是语音放入总音轨的位置；`end` 为测得的片段末端；`sceneEnd` 包含读图/预测停顿。`duration` 包含 intro/tail。相邻画面窗口宜连续；未描述的空隙不能在合成时默默丢掉。

cue ID 唯一、各语言顺序相同；时间为有限数且 `0 <= start <= end <= sceneEnd <= duration`。实用 cue 的画面窗口须大于零。模板的 `provisional: true` 时钟仅供分镜，真实交付替换为实测时间并保留测量证据，不能只删除标记。

```js
const p = clamp((time - cue.start) / (cue.sceneEnd - cue.start), 0, 1);
const positions = interpolate(before, after, ease(p));
const score = metrics(positions, constraints);
```

数字与几何同源。旁白在末半句报终值时，让几何先到终点再保持。例如前30%移动、后70%读数，不必全句都运动。

## 确定性与随机访问

`renderAt(t)` 直接生成任意时刻画面。下面路径应一致：

```text
renderAt(12.3)
renderAt(2); renderAt(27); renderAt(12.3)
fresh page → renderAt(12.3)
```

不依赖 `Date.now()`、上一帧位置、累加粒子、未设种子随机数或自行运行的 CSS animation。可用纯函数轨迹、固定种子、显式 Web Animations `currentTime`，或由 `t` 写 CSS 变量。

字体和图片准备好再拍帧；固定16:9尺寸、设备缩放和字体。PNG保留细字，JPEG管道更快但有损；必须看实际编码画面。组件可返回SVG或DOM，关键是相同状态一致渲染。

## 精确移交实验

```js
{cueId, progress, positions, constraints, mode,
 selectedNet, traceIndex, phase, parameters, origin:"video-snapshot"}
```

先暂停影片，再取当前音色的 `stateAt(video.currentTime, clock, script)`，深拷贝传递。传中间帧实际坐标，不能跳到“本章预设”。`traceIndex` 是轨迹定位，不代替仍在插值的 `positions`。

实验接收中间帧后显示“Transferred video state”。按下一算法步时明确回到哪个离散步骤，不把插值坐标标成真实迭代结果。参数改变从同一 starter 重算以公平比较。

容量、固定点、边界一起传递。Placement 的 capacity 2 设计例与 capacity 1 参考实验不能只换坐标不换约束；同理适用于其他混用实验设定的课程。

## 切音色保留语义位置

```text
t_target = target[cueId].start + progress × (target[cueId].sceneEnd − target[cueId].start)
```

保留字幕、倍速、播放/暂停。异步切源用递增 request token，旧 `loadedmetadata` 不能覆盖新选择；加载中保存 pending cue/progress，不能从未加载好的 currentTime 推算。章节查当前配音的 cue 起点，不固定所有声音版的分钟秒数。

intro/tail 映射单独定义。加载失败禁用移交、给可操作错误；不静默回退到错误音色。

## 多种正确答案

题型按目标选：读图/算数、预测动作、诊断失败、满足约束、比较算法。实践题用 `grade(state)` 检查锚点、容量、合法坐标与指标，允许多个满足条件的布局，不能把视频终帧当唯一答案。

数值容差明确单位。先检查理论下界；例如总容量小于对象数时零溢出不可能。反馈说明哪条约束未满足。题目“回看”关联 cue ID，“试一试”关联带约束的状态。
