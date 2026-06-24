<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Platform-Windows_|_macOS-lightgrey" alt="Platform Win/Mac">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License MIT">
  <img src="https://img.shields.io/badge/预设项目-69-blue" alt="69 preset projects">
</p>

<h1 align="center">🤖 AI Updater</h1>
<p align="center"><strong>一行命令，找到并更新你电脑上所有的 AI 开源软件。</strong></p>

<p align="center">
  <a href="README.md">English</a>
</p>

---

## 痛点

你电脑上装了一大堆 AI 项目——ComfyUI、Ollama、Open WebUI、Langflow、Stable Diffusion WebUI、text-generation-webui……到底哪些有新版？哪些是 git 拉的、pip 装的、brew 安的还是 winget 下的？你甚至都忘了自己装过什么。

## 解决方案

`ai-updater` 扫描你的整台电脑——目录 + 包管理器——把所有的 AI 相关项目（包括你忘了的）全揪出来，检查有没有更新，然后一键升到最新。

```bash
pip install -r requirements.txt
python ai_updater.py
```

## 效果演示

```
[扫描] 目录扫描 (Windows)
  -> D:\AIwkspace
    ✓ ComfyUI  (a1b2c3d)  [D:\AIwkspace\ComfyUI]
    ✓ Open WebUI  (v0.3.23)  [D:\AIwkspace\open-webui]

[扫描] pip (Python)
  -- 智能发现 --
  ! [发现] gradio (6.15.2)  -> 6.19.0
  ! [发现] torch (2.12.0)   -> 2.12.1
  ! [发现] transformers (5.9.0) -> 5.12.1
    pip 智能发现 9 个 AI 相关包

[扫描] winget (Windows)
  - [发现] Ollama (0.30.3)

[预设项目] 来自 projects.csv — 共 2 个         ← 从数据库匹配
[智能发现] AI 关键词匹配 — 共 10 个              ← 自动发现

  可更新: 6   已最新: 6   总计: 12

你想升级哪些？
  【1,3,5】 选序号  【1-5】 范围  【all】 全部  【p】 仅预设  【d】 仅发现  【q】 退出
> 
```

## 核心能力

### 双层检测

| 层 | 原理 |
|---|---|
| **预设匹配**（69 项目） | 扫描目录找 git 仓库 + 特征文件，与 `projects.csv` 匹配。同时检查 pip/brew/winget/conda 中关联的包。 |
| **智能发现** | 遍历**所有已安装的包**（pip, npm, brew, winget, conda），用 AI 关键词匹配——torch、transformers、langchain、gradio、whisper、chroma、ollama 等——把 CSV 里没有的也揪出来。 |

### 智能更新引擎

- **Git 项目**：`git stash`（保护本地修改）→ `git pull` → 执行更新后命令（如 pip install requirements）
- **pip 包**：`pip install --upgrade` + PyPI API 版本比对
- **Homebrew**：`brew upgrade`
- **winget**：`winget upgrade`
- **conda/npm**：检测并报告

### 交互式选择

扫描结束后，你来决定升级哪些：
- `p` — 只升预设项目（安全，来自你的 CSV 数据库）
- `d` — 只升智能发现的包
- `1,3,5` — 手动挑序号
- `all` — 全部一起升

### 跨平台

| 平台 | 包管理器 |
|---|---|
| **Windows** | pip · npm · winget · conda |
| **macOS** | pip · npm · brew · conda |

## 快速开始

```bash
# 1. Clone
git clone https://github.com/YOU/ai-updater.git
cd ai-updater

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python ai_updater.py

# 首次运行自动生成 config.yaml，编辑它来添加你自己的扫描路径
```

## 添加你自己的项目

用 **Excel / WPS / Google Sheets** 打开 `projects.csv`——它就是一个表格！在末尾新增一行：

| name | category | git_url | dir_signature | website | update_method | platforms |
|---|---|---|---|---|---|---|
| 我的项目 | llm-tools | github.com/my/project | myproject/main.py | https://... | git_pull | win\|mac |

每次运行时脚本会自动读取，无需改代码。

## 预设项目（69 项，5 大类）

| 类别 | 数量 | 示例 |
|---|---|---|
| 🎨 图像生成 | 15 | ComfyUI、AUTOMATIC1111、Forge、Fooocus、InvokeAI、SwarmUI、FaceFusion |
| 🧠 LLM 工具 | 20 | Ollama、Open WebUI、text-gen-webui、llama.cpp、vLLM、GPT4All、Jan |
| 🔧 AI 框架 | 16 | Langflow、Dify、Flowise、AutoGPT、CrewAI、MetaGPT、LangChain、LlamaIndex |
| 🎤 语音 AI | 9 | Whisper.cpp、Coqui TTS、Bark、RVC-WebUI、GPT-SoVITS、ChatTTS |
| 🗂️ 向量数据库 | 9 | Chroma、Qdrant、Milvus、Weaviate、PGVector、LanceDB |

## 原理解析

```
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│  扫描    │ -> │   识别    │ -> │  版本对比 │ -> │  一键升级 │
│  目录    │    │  CSV 匹配 │    │  git/PyPI│    │  用户选择 │
│  +包管理 │    │  +关键词  │    │  /brew   │    │  git pull │
│          │    │  智能发现 │    │  API     │    │  /pip upg │
└──────────┘    └───────────┘    └──────────┘    └──────────┘
```

## 依赖

- Python 3.8+
- Git（用于 git 项目）
- `pip install -r requirements.txt`

## 常见问题

**Q: 会弄坏我的本地修改吗？**  
A: 不会。Git 项目在 pull 前自动 `git stash`。pip 包安全升级。所有操作可逆。

**Q: 能忽略某些项目不检查吗？**  
A: 可以。在 `config.yaml` 的 `ignore_projects` 里加上项目名。

**Q: 69 个预设里没有我的项目怎么办？**  
A: 智能发现会自动从包管理器里抓到 AI 相关的包。你也可以加到 `projects.csv`。

**Q: 支持 Linux 吗？**  
A: 暂时不支持，欢迎 PR！

## License

MIT — 详见 [LICENSE](LICENSE)。
