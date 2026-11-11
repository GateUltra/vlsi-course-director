# 可迁移的渲染、时间轴和验收工具

这些脚本从 Placement Lesson 06 的真实制作链路中抽取，路径、端口、浏览器和音色均由参数决定。它们不调用在线 TTS，也不下载资源。新的课程需要先完成自己的 domain、scene、script 和配音时钟。

## 依赖与目录

- `serve_site.py` 与基础检查只需要 Python 3.10+。
- 渲染需要 Python `playwright` 及 Chromium；可安装 Playwright 自带 Chromium，也可用 `--browser` 指定已有 Chrome。FFmpeg/ffprobe 应在 PATH 上，或使用同名参数显式指定。
- 影片编码使用 H.264 / yuv420p，宽高必须为偶数。默认 1920×1080 / 30 fps，可调整。
- 脚本之间使用同目录导入，复制时保留整个 `scripts/`，至少保留 `validate_media.py`。
- 成片必须使用实际测量的配音时长；starter 中的示范时钟只供分镜与组件演示。

下面的命令假设项目根目录有 `site/`、`production/`，技能脚本已复制到项目 `tools/`。这些目录名是示例，可以换成实际路径。先用一小段真实内容验证，再渲染全片。

```powershell
python tools/serve_site.py --directory site --port 8770
```

服务器只监听 `127.0.0.1`，支持单区间 HTTP Range、HEAD、尾部区间，以及正确的 416 响应；拒绝逃出预览根目录的符号链接。它是本地预览服务器，不是公网生产服务器。网页使用相对资源路径，不依赖这个端口。

## 页面契约

独立的 `render.html` 暴露：

```js
window.ready = true;                    // 数据与组件已初始化
window.clock = clock;                   // 建议暴露正在使用的实际时钟
window.renderAt = (seconds) => {        // 可以返回 Promise
  const state = stateAt(seconds, clock, script);
  stage.innerHTML = Scene(state);
};
```

`renderAt(t)` 应从时间直接算出完整状态。不能依赖“上一帧加了多少”、真实 `Date.now()`、随机粒子历史、累积 CSS transition 或正在运行的动画计时器。粒子需要固定 seed 或显式时间函数；字体使用稳定的本地资源。将相同时间重复渲染、倒序渲染，再比较，才能发现仅顺序播放正常的实现。

工具会等待 `document.fonts.ready` 和页面中的图片解码，按 `t = frame / fps` 调用接口，再截图送给 FFmpeg。若页面暴露了 `window.clock`，会先逐项比较其总时长、cue ID 和 `start/end/sceneEnd` 是否与 `--clock` 一致；不同就停止，避免 URL 仍选择英式而参数已经换成中文时钟。未暴露 `window.clock` 的页面仍可渲染，但调用者必须自行验证页面与命令行使用同一个时钟，报告的 `pageClockChecked` 此时为 false。工具不会自动修复不确定的页面动画，也不会帮 DOM 里的动画找正确时刻。后台计时器被节流之外的时间行为仍应由场景代码消除。

```powershell
# 先检查每个 cue 的中间帧；也可显式给出 --preview-times "0,2.5,7.9"
python tools/render_html.py --url http://127.0.0.1:8770/render.html --clock site/media/timings/en_gb.json --preview-dir review/frames

# 渲染主要音轨的静音画面
python tools/render_html.py --url http://127.0.0.1:8770/render.html --clock site/media/timings/en_gb.json --output production/picture-en_gb.mp4
```

输出旁边有 `.render.json`，记录帧数、帧率、尺寸、耗时和页面错误。默认拒绝覆盖已有 MP4；明确需要重建时传 `--overwrite`。编码失败或页面错误时不会把临时文件替换为最终 MP4。HTTP 资源错误也会使渲染失败。

## 配音时钟与逐 cue 重定时

统一时钟结构为：

```json
{
  "id": "en_gb",
  "duration": 9.8,
  "segments": [
    {"id": "motivation", "start": 0.4, "end": 4.1, "sceneEnd": 4.4},
    {"id": "comparison", "start": 4.4, "end": 9.1, "sceneEnd": 9.4}
  ]
}
```

`start..end` 是配音区间；`end..sceneEnd` 是说完后的停顿。初始 `0..first.start` 为开场，`last.sceneEnd..duration` 为片尾。cue ID 唯一且在所有配音中保持同序。`start ≤ end ≤ sceneEnd`，场景区间必须相接；额外停顿应包含在 `sceneEnd` 中，不能留下没有定义的中间空洞。

新音色使用自己的测量时钟，而不是沿用英文秒数：

```powershell
python tools/retime_video.py --source production/picture-en_gb.mp4 --source-clock site/media/timings/en_gb.json --target-clock site/media/timings/zh.json --audio production/zh/mix.wav --output site/media/lesson-zh.mp4
```

脚本将每个语义片段的**画面**变速到目标片段长度，配音保持原来的速率。`--audio` 是含开头、停顿和结尾的完整目标 WAV；只有逐句 MP3 时不能直接传入。暂不合成声音可以省略 `--audio`，得到静音 MP4。主音色也可以源时钟与目标时钟相同运行此步骤来合成音轨；这会再编码一次画面，若需要无损复制主画面，可直接用 FFmpeg `-c:v copy` 做 mux。

帧边界从**累计时间**量化，例如 `round(sceneEnd * fps)`；只对最后完整片尾采用 `ceil`，不能单独把每一段的时长四舍五入后相加。后者会在 39 段之后积累明显误差。脚本逐段检查实际编码帧数，在 `.retime.json` 中保留每段源/目标边界。

以下情况会报错而不是静默截断：cue 缺失/顺序不同、时间不合法、未表达的中间空洞、源帧率不一致、影片与源时钟长度不符、目标完整音频长度不符、一侧存在而另一侧缺失的开头/片尾、短到量化后零帧的区间。此时应修正时钟或直接按目标时钟重新渲染。

**适用范围**：数学图、模块移动、解释性角色手势等以 cue 内归一化进度驱动的动画。英语和中文在同一 cue 内词序不一样；仅凭 cue 变速不能保证指词、音节或唇形级对齐。需要“念到这个词才指向它”的片段，应细分 cue 或按该语言的实际标记重新渲染。不要称为“精确口型同步”。

## 成片检查与能力边界

manifest 结构采用完整课程的约定：

```json
{
  "defaultVoice": "en_gb",
  "captionLanguages": ["en", "zh"],
  "tracks": [
    {
      "id": "en_gb",
      "video": "media/lesson-en_gb.mp4",
      "timing": "media/timings/en_gb.json",
      "captions": {"en": "media/captions/en_gb-en.vtt", "zh": "media/captions/en_gb-zh.vtt"}
    }
  ]
}
```

资源均相对于网站根目录。工具拒绝远程 URL、缺失/空文件和逃出根目录的路径。

```powershell
python tools/validate_media.py --site site --decode --report review/media.json
```

检查范围：音轨 ID、defaultVoice、所有时钟的 cue 顺序与连续性、每条影片同时含图像与声音、帧率、容器及视频/音频各自与时钟的长度、明显的音视频非零起点、声明的字幕语言是否齐全、VTT 时间与文本非空、字幕重叠和越界。图像流允许一帧加 10 ms 的边界误差；声音流允许 50 ms 的编码/尾部边界误差。缺少可核验的流时长会报错，不用容器总时长替代。最终成片检查拒绝带 `provisional: true` 的分镜时钟；静音分镜渲染仍可使用这种时钟。`--decode` 会完整解码图像与声音以发现损坏数据；不带时只读取媒体元数据。

VTT 工具采用 `HH:MM:SS.mmm` 格式，不自动改写或翻译。它不判断字幕断句是否拆开了 `48.1`、字符行长、翻译术语或配音语义。这些需要在字幕生成器和课程 QA 中单独检查。它也不测量音量、试听发音、计算音频与母带互相关，或检查网页切换/全屏行为。把报告称作“机械检查”，不要称作“全部验收”。

## 已运行的工具回归

```powershell
python tools/check_tooling.py
python tools/check_tooling.py --integration --browser "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

基础检查覆盖合法时钟、缺失/重复/错序 ID、重叠、空洞、NaN、无开场片尾的累计帧数、VTT 越界、本地路径限制、HTTP 部分 GET/HEAD 和 416。

完整检查在临时目录生成一个 320×180 的确定性 HTML 场景，实际渲染 1.8 秒 / 18 帧，将两段语义画面变为 2.2 秒 / 22 帧，合成未变速的合成测试音，完整解码并验证最终 manifest。还会故意输入错误页面时钟，确认失败时保留原输出；生成容器长度正确但声音仅 0.2 秒或图像仅 1.8 秒的坏片，确认分别被拒绝；并验证临时时钟不能用于最终成片验收。测试结束清理临时目录；不触碰课程源文件、不发送在线请求。这是工具烟雾测试，不替代真实课程的 1080p 画面审查。

打包时已在 Windows / Python 3.11 / 本地 Chrome / FFmpeg 环境运行通过上述完整检查；另对实际 Placement 成片的 4 个视频与 28 个 VTT 运行了通用验证，全部通过。当前环境的沙箱需要授权启动本地浏览器与套接字；安装后的普通本地终端不一定有这个限制。
