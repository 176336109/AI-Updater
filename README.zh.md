<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Skill-blueviolet?logo=claude&logoColor=white" alt="Claude Code Skill">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Platform-Windows_|_macOS-lightgrey" alt="Platform Win/Mac">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License MIT">
  <img src="https://img.shields.io/badge/%E9%A2%84%E8%AE%BE%E9%A1%B9%E7%9B%AE-229-blue" alt="229">
</p>

<h1 align="center">AI Updater</h1>
<p align="center"><strong>Claude Code Skill：一键找到并升级你电脑上所有的 AI 开源软件。</strong></p>

<p align="center">
  <a href="README.md">English</a>
</p>

---

## 痛点

你半年前 `git clone` 了 ComfyUI。然后用 `winget` 装了 Ollama。然后又装了 Stable Diffusion WebUI、又 `pip install` 了十几个包——torch、transformers、gradio、langchain……后来又 clone 了一堆 GitHub 上的 Claude Code skills。有的在 git repo 里吃灰，有的散落在 venv 里，有的是 winget 装的，从来没更新过。

**到底哪些过时了？电脑上到底装了些什么？你完全不知道。**

一个一个打开项目目录 `git pull`、`pip list` 对比 PyPI、`winget upgrade` 检查——一个下午就没了。

## 解决方案

在 Claude Code 里敲一行斜杠命令：

```
/ai-updater
```

它会一次性扫描你的整台电脑——目录 + 包管理器——找出你所有的 AI 相关项目（包括你忘了的），检查哪些可以更新，然后让你一键升级。

## 效果

```
============================================================
| AI Updater  --  一键更新你的 AI 开源工具箱
|==========================================================|
已加载 229 个预设项目（projects.csv）

[扫描] 目录扫描 (Windows)
  -> D:\AIwkspace
    v ComfyUI  (a1b2c3d)  [D:\AIwkspace\ComfyUI]

[扫描] pip (Python)
  -- 智能发现 --
  ! [发现] torch (2.12.0)  -> 2.12.1
  ! [发现] transformers (5.9.0) -> 5.12.1
  ! [发现] gradio (6.15.2)  -> 6.19.0
    pip 智能发现 9 个 AI 相关包

[扫描] winget (Windows)
  - [发现] Ollama (0.30.3)
  - [发现] Figma (126.2.7)

[预设项目] from projects.csv -- 1 个
[智能发现] AI 关键词匹配 -- 11 个

  可更新: 7   已最新: 5   总计: 12

你想升级哪些？
  [1,3,5] 选序号  [1-5] 范围  [all] 全部  [p] 仅预设  [d] 仅发现  [q] 退出
>
```

选好序号，剩下的它帮你干：`git pull`、`pip install --upgrade`、`brew upgrade`、`winget upgrade`。

## 安装

```bash
git clone https://github.com/176336109/AI-Updater.git
cd AI-Updater

# 运行安装器（自动检测你装的 AI 工具）
bash install.sh        # macOS / Linux
# install.bat           # Windows

# 安装 Python 依赖
pip install -r requirements.txt
```

安装器自动把 skill 复制到对应工具的配置目录：

| 工具 | 安装位置 |
|---|---|
| **Claude Code** | `~/.claude/skills/ai-updater/` + `~/.claude/commands/` |
| **Codex** | `~/.codex/skills/ai-updater/` + `~/.codex/commands/` |
| **Cursor** | `~/.cursor/commands/` |

然后打开你的 AI 编程工具，敲 `/ai-updater`。

## 为什么做成 Claude Code Skill

你本来就泡在 Claude Code 里。不用切终端，直接敲 `/ai-updater`，Claude Code 帮你扫、比对、升级。某个项目更新失败了？错误信息就在会话里，直接让 Claude Code 帮你修。

## 核心能力

### 预设匹配 + 智能发现

| 层 | 原理 |
|---|---|
| **预设匹配（229 项目）** | 扫描目录找 git 仓库，与 `projects.csv` 匹配。检查 pip/brew/winget/conda 中关联的包。 |
| **智能发现** | 遍历 pip/npm/brew/winget/conda 中**所有已装包**，用 AI 关键词匹配——torch、transformers、langchain、gradio、whisper、chroma、ollama、figma、deepseek、grok…… |

### 更新引擎

- **Git 项目**：`git stash` -> `git pull` -> 更新后命令
- **pip**：`pip install --upgrade` + PyPI 版本比对
- **brew**：`brew upgrade`
- **winget**：`winget upgrade`
- **conda / npm**：检测并报告

### 你说了算

扫描结束后，**你**决定升哪些：
- `p` — 只升预设项目
- `d` — 只升智能发现的包
- `1,3,5` — 手动挑序号
- `all` — 全部一起升
- `q` — 不升退出

### 跨平台

| 平台 | 包管理器 |
|---|---|
| **Windows** | pip · npm · winget · conda |
| **macOS** | pip · npm · brew · conda |

## 独立模式

不想在 Claude Code 里用？直接跑脚本：

```bash
python ai_updater.py                  # 扫描 + 交互升级
python ai_updater.py --scan-only      # 只扫描
python ai_updater.py --update-all     # 自动全部升级
python ai_updater.py --config my.yaml # 指定配置
```

## 添加你自己的项目

用 Excel / WPS / Google Sheets 打开 `projects.csv`，在末尾新增一行：

| name | category | git_url | dir_signature | website | update_method | platforms |
|---|---|---|---|---|---|---|
| 我的项目 | llm-tools | github.com/my/project | myproject/main.py | https://... | git_pull | win\|mac |

Skill 每次运行自动读取，无需改代码。

## 预设项目（229 项，11 大类）

| 类别 | 数量 | 示例 |
|---|---|---|
| 图像生成 | 25 | ComfyUI、AUTOMATIC1111、Forge、Fooocus、InvokeAI |
| LLM 工具 | 29 | Ollama、Open WebUI、text-gen-webui、llama.cpp、vLLM |
| AI 框架 | 27 | Langflow、Dify、Flowise、AutoGPT、CrewAI、LangChain |
| 语音 AI | 17 | Whisper.cpp、Coqui TTS、Bark、RVC-WebUI、ChatTTS |
| 向量数据库 | 12 | Chroma、Qdrant、Milvus、Weaviate、PGVector |
| AI 编程助手 | 3 | Aider、Continue、Cline |
| AI 记忆 | 51 | Mem0、Letta、Cognee、Graphiti、MemoryOS |
| RAG 框架 | 5 | RAGFlow、Quivr、Verba、Cognita、AgentGPT |
| 代码图谱 | 8 | codegraph、GitNexus、code2prompt |
| Token 优化 | 35 | LLMLingua、Headroom、RouteLLM、tiktoken、Langfuse |
| 设计工具 | 17 | Open Design、screenshot-to-code、oh-my-mermaid、penpot、remotion |

## 原理解析

```mermaid
flowchart LR
    A[扫描<br/>目录<br/>+包管理] --> B[识别<br/>CSV 匹配<br/>+关键词<br/>智能发现]
    B --> C[版本对比<br/>git / PyPI<br/>/ brew]
    C --> D[一键升级<br/>用户选择<br/>git pull<br/>/ pip upg]
```

## 常见问题

**Q: 会弄坏我的本地修改吗？**  
A: 不会。Git 项目在 pull 前自动 `git stash`。pip 包安全升级。

**Q: 能忽略某些项目吗？**  
A: 可以。在 `config.yaml` 的 `ignore_projects` 里加上项目名。

**Q: 229 个预设里没有我的项目怎么办？**  
A: 智能发现会自动从包管理器抓出来。也可以加到 `projects.csv`。

**Q: 支持 Linux 吗？**  
A: 暂不支持，欢迎 PR！

## License

MIT — 详见 [LICENSE](LICENSE)。
