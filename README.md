<div align="center">

<h1>Video Knowledge Notes</h1>

<p><strong>把知识视频整理成可以独立阅读、理解与复用的 Markdown 笔记</strong></p>

<p>适用于 WorkBuddy 等支持本地 Skill 工作流的 AI Agent · 面向 Obsidian 与通用 Markdown 阅读环境</p>

<p>
  <img src="https://img.shields.io/badge/Release-v1.0.0-2563eb?style=flat-square" alt="Release v1.0.0" />
  <img src="https://img.shields.io/badge/Type-Agent%20Skill-16a34a?style=flat-square" alt="Agent Skill" />
  <img src="https://img.shields.io/badge/Notes-Markdown-334155?style=flat-square" alt="Markdown" />
  <img src="https://img.shields.io/badge/Language-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-64748b?style=flat-square" alt="简体中文" />
</p>

<p><a href="#功能介绍">功能介绍</a> · <a href="#安装与使用">安装与使用</a> · <a href="#平台支持">平台支持</a> · <a href="#项目结构">项目结构</a></p>

</div>

---

## 项目简介

Video Knowledge Notes 是一个面向 **知识类视频** 的 AI Agent Skill。它将用户提供的视频链接、本地音视频或现成字幕，整理为详细、独立可读的**简体中文 Markdown 知识笔记**。

它不追求把一小时的视频压缩成几条结论，而是尽可能保留视频中的**概念、推理过程、案例、关键数字与适用边界**，让读者不必重新打开视频，也能理解和复用其中的知识。

> **这不是独立软件。** 本仓库不提供桌面客户端、Web 页面或独立的视频转写服务。`SKILL.md` 定义工作流程，Agent 负责调用脚本、已有工具及模型完成任务。

## 功能介绍

| 能力 | 说明 |
| --- | --- |
| **优先获取现成字幕** | 首先复用用户提供的字幕、已有缓存或平台字幕，避免无意义的全片转写。 |
| **B 站中文字幕获取** | 内置 Python 脚本，支持 B 站 BV 视频链接及指定分 P，保留字幕时间轴。 |
| **按需登录与会话复用** | 通过专用浏览器正常登录；在本机保留会话，不要求把密码或 Cookie 粘贴到聊天中。 |
| **无字幕时备用处理** | 在用户授权且环境具备能力时，由 Agent 选择现有的本地识别或云端转写工具。 |
| **重点核查** | 关注重要数字、否定词、术语、因果关系及字幕遗漏，必要时局部核对。 |
| **详细知识笔记** | 保留关键概念、推导、案例与解释，并明确区分原视频内容和补充分析。 |
| **自定义学习规则** | 可以使用自带的学习系统说明，也可以让 Agent 按用户指定的学习方法组织内容。 |
| **Markdown 交付** | 输出可直接阅读的 `.md` 文件，适合放入 Obsidian，不依赖专用笔记插件。 |

### 和普通视频摘要有什么不同？

- **先完整理解，再整理**：不只提取关键词和结论，而是解释为什么得到这些结论。
- **忠于原始材料**：区分视频作者的主张、可核实事实、整理者补充与尚不确定的部分。
- **避免重复计算**：已有完整字幕时跳过媒体下载和转写；只有必要时才处理音频或画面。
- **不过度模板化**：章节由知识内容决定，不强制给每段添加反例、迁移或思维导图。

## 平台支持

| 输入来源 | 当前能力 | 说明 |
| --- | --- | --- |
| 用户提供的字幕或文字 | 支持 | Agent 直接读取并整理。 |
| Bilibili（B 站） | 内置字幕获取脚本 | 读取平台可用的中文字幕；支持 BV 链接和分 P，实际结果受平台接口及权限影响。 |
| 本地音视频 | 条件支持 | 由 Agent 使用当前环境可用的识别或处理工具；本仓库未内置完整的通用媒体转写引擎。 |
| YouTube 等其他平台 | 依赖外部工具 | Agent 可先尝试其现有字幕获取能力；本仓库没有提供已验证的通用适配器。 |
| 抖音、小红书 | 仅提供专用浏览器登录入口 | 尚未实现对应平台的专用字幕提取接口，不等于已经支持自动提取字幕。 |

**重要**：登录失败、接口异常与“视频确实没有字幕”是不同情况。本 Skill 不会因一次请求失败就认定必须重新转写整段视频。

## 安装与使用

### 方式一：作为 Agent Skill 使用（推荐）

1. 点击仓库右上角的 **Code → Download ZIP**，下载并解压；或使用 Git 克隆仓库。
2. 将整个 `video-knowledge-notes` 目录放入你的 Agent 所支持的 **Skill 目录**，保留 `SKILL.md`、`scripts/` 和 `references/` 的相对位置。
3. 按 Agent 的 Skill 发现机制启用该目录，并确认其能够读取 `SKILL.md`。
4. 向 Agent 提供视频链接、本地文件或字幕，并说明要生成知识笔记。

> 主要针对 WorkBuddy 工作流编写。其他 Agent 是否能自动发现并执行该 Skill，取决于对应产品的 Skill 机制、权限和工具环境；不能仅凭目录存在就保证兼容。

### 使用示例

向 Agent 发出以下类型的请求即可：

> 请用 video-knowledge-notes 整理这个 B 站视频：[视频链接]。保留核心概念、推理过程和案例，输出一份可以独立阅读的简体中文 Markdown 笔记。

> 我已经有这段课程的视频字幕，请直接根据字幕生成详细学习笔记，不要重新下载或识别视频。

> 这是一段本地课程视频。请先检查是否已有字幕；如果需要转写，先告诉我当前可用的方式。

### 方式二：单独运行 B 站字幕获取脚本

若只需要使用内置字幕获取能力，可在仓库目录运行 Python 脚本。先确保使用的 Python 环境安装了 `playwright`，并具备可供 Playwright 使用的浏览器。

```powershell
python -m pip install playwright
```

如果已有 Edge 或 Chrome，可用 `--channel msedge` 或 `--channel chrome` 指定；也可以在用户同意后安装 Playwright Chromium：

```powershell
python -m playwright install chromium
```

获取 B 站视频的现成中文字幕（将示例 BV 号替换成真实视频编号）：

```powershell
python -X utf8 scripts/browser_subtitles.py fetch "https://www.bilibili.com/video/BVxxxxxxxxxx/?p=1" --output "./sources/demo"
```

如果平台确实要求登录，可通过专用浏览器完成登录，再重新运行获取命令：

```powershell
python -X utf8 scripts/browser_subtitles.py login bilibili --channel msedge
```

成功获取后会生成 `subtitle.json`、`subtitle.txt` 与 `subtitle.srt` 等文件。**这个脚本只负责获取字幕，不会单独生成最终知识笔记**；笔记整理仍由 Agent 按 Skill 规则完成。

完整细节见 [字幕获取说明](references/acquisition.md)。

## 笔记产出

默认产物为以主题命名的 Markdown 文件，例如：

```text
学习主题.md
sources/
  subtitle.json
  subtitle.txt
  subtitle.srt
```

笔记尽量覆盖：

- 视频实际讨论的问题、核心结论及适用范围；
- 必要的概念定义、推理步骤和因果关系；
- 关键案例、数值、前提与具体解释；
- 能帮助理解、但清楚标明来源的补充知识；
- 适量的来源链接和时间段，便于核对原视频。

笔记默认不生成 PDF、图片版或思维导图，也不会擅自写入用户未知的 Obsidian 仓库。

## 项目结构

```text
video-knowledge-notes/
├── SKILL.md                         # Skill 主入口及工作流程
├── scripts/
│   └── browser_subtitles.py         # B 站字幕获取与专用浏览器登录
└── references/
    ├── acquisition.md               # 字幕获取与登录
    ├── fallback.md                  # 无字幕时的备用方案
    ├── personal-learning-system.md   # 默认学习规则
    ├── note-writing.md              # 笔记生成与质量标准
    └── accepted-note.md             # 笔记质量参考样例
```

## 隐私与依赖

- 登录状态保存在本地独立的浏览器数据目录中，不应提交到 GitHub 或知识库。
- 不要求用户向 Agent 提供账号密码，也不要求在聊天中粘贴 Cookie。
- 仅在需要时检查或安装相关工具，不预先安装完整的语音识别、OCR 或视频下载工具链。
- 如果备用方案涉及云端上传或付费 API，应先取得用户授权。
- 视频平台接口、字幕可用性、网络环境及账号权限均可能影响实际结果。

## 参考文档

- [Skill 工作入口](SKILL.md)
- [字幕获取与登录](references/acquisition.md)
- [备用转写方案](references/fallback.md)
- [个人学习系统通用说明](references/personal-learning-system.md)
- [笔记生成指南](references/note-writing.md)
- [笔记质量参考样例](references/accepted-note.md)

---

<div align="center">
<p><strong>Video Knowledge Notes · v1.0.0</strong></p>
<p>让视频知识成为可以长期阅读、理解和复用的笔记。</p>
</div>
