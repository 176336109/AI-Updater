#!/usr/bin/env python3
"""
AI Updater -- 一键检测并更新电脑上所有 AI 开源软件
==============================================
跨平台（Win + Mac）| 50+ 预设项目 | 交互式更新

用法:
    python ai_updater.py                  # 扫描 + 交互更新
    python ai_updater.py --scan-only      # 只扫描不更新
    python ai_updater.py --update-all     # 扫描后自动全部更新
    python ai_updater.py --config my.yaml  # 使用指定配置文件

依赖: pip install colorama requests pyyaml packaging
"""

import argparse
import csv
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# -- 可选依赖 ----------------------------------------------
try:
    import yaml
except ImportError:
    yaml = None

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # 哑替代
    class _Dummy:
        def __getattr__(self, _):
            return ""
    Fore = Style = _Dummy()

try:
    from packaging.version import parse as version_parse
except ImportError:
    import requests as _requests_  # will be used fallback
    version_parse = None

# -- 常量 --------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECTS_CSV = SCRIPT_DIR / "projects.csv"
CONFIG_YAML = SCRIPT_DIR / "config.yaml"
DEFAULT_CONFIG_YAML = "config.yaml"

OS_NAME = platform.system().lower()  # "windows" | "darwin" | "linux"
IS_WIN = OS_NAME == "windows"
IS_MAC = OS_NAME == "darwin"

# -- AI 关键词 -- 用于在包管理器中智能发现未在 CSV 中收录的 AI 包 --
AI_KEYWORDS = {
    # 深度学习框架
    "torch", "pytorch", "tensorflow", "jax", "keras", "mxnet", "oneflow",
    "paddlepaddle", "mindspore", "theano", "caffe",
    # transformers 生态
    "transformer", "llama", "gpt", "bert", "t5", "bloom", "falcon", "mistral",
    "gemma", "qwen", "chatglm", "baichuan", "yi-", "deepseek",
    # AI 库 / 工具
    "langchain", "llamaindex", "chromadb", "qdrant", "milvus", "weaviate",
    "pinecone", "faiss", "lancedb", "pgvector", "txtai",
    "diffuser", "stable-diffusion", "comfy", "sd-webui",
    "whisper", "coqui", "tts", "bark", "vocoder", "voice",
    "instruct", "peft", "lora", "qlora", "fine-tune", "rlhf", "dpo",
    "openai", "anthropic", "claude", "gemini", "copilot", "chatgpt",
    "embedding", "tokenizer", "sentencepiece", "huggingface",
    "vllm", "ollama", "gguf", "ggml", "exllama", "autogptq",
    "agent", "autogen", "crewai", "metagpt", "semantic-kernel",
    "onnx", "tensorrt", "openvino", "coral",
    "gradio", "streamlit", "chainlit", "mesop",
    "ray", "deepspeed", "megatron", "colossal",
    "spacy", "nltk", "gensim", "allennlp",
    # Design / UI
    "penpot", "remotion", "framer", "figma", "sketch", "mermaid",
    "drawio", "draw.io", "design-system", "frontend-design",
    # CV
    "opencv-python", "pillow-simd", "albumentations", "detectron",
    "yolo", "ultralytics", "mmdet", "mmseg",
    # NLP
    "jieba", "pkuseg", "hanlp", "lac",
}
AI_PKG_SET = {k.lower().replace("-", "_") for k in AI_KEYWORDS}

# 部分匹配关键词（包名中包含即命中）
AI_SUBSTRINGS = [
    "llm", "gpt", "bert", "t5", "bloom", "llama", "mistral", "falcon",
    "gemma", "qwen", "chatglm", "baichuan", "yi-", "deepseek",
    "langchain", "chroma", "qdrant", "milvus", "weaviate",
    "diffus", "whisper", "stablediffusion", "sd-webui",
    "tts", "bark", "coqui", "vocoder",
    "vllm", "ollama", "gguf", "ggml", "exllama", "autogptq",
    "embedding", "tokenizer", "huggingface",
    "autogen", "crewai", "metagpt", "semantic-kernel",
    "onnx", "tensorrt", "openvino",
    "gradio", "streamlit", "chainlit",
    "deepspeed", "megatron",
    "transformer",
]

def _is_ai_package(name: str) -> bool:
    """判断包名是否属于 AI 相关"""
    key = name.lower().replace("-", "_")
    # 精确匹配
    if key in AI_PKG_SET:
        return True
    # 部分匹配
    for sub in AI_SUBSTRINGS:
        if sub in key:
            return True
    return False


# ===========================================================
@dataclass
class Project:
    """来自 projects.csv 的一行"""
    name: str
    category: str
    git_url: str          # 关键词，| 分隔
    dir_signature: str    # 特征文件/目录，| 分隔
    website: str
    update_method: str    # git_pull / pip_upgrade / brew_upgrade / winget_upgrade / manual
    platforms: str        # win | mac | win|mac
    brew_name: str
    winget_id: str
    pip_packages: str     # | 分隔
    post_update: str      # | 分隔的命令

    def git_urls(self) -> list[str]:
        return [x.strip() for x in self.git_url.split("|") if x.strip()]

    def dir_sigs(self) -> list[str]:
        return [x.strip() for x in self.dir_signature.split("|") if x.strip()]

    def pip_pkgs(self) -> list[str]:
        return [x.strip() for x in self.pip_packages.split("|") if x.strip()]

    def post_cmds(self) -> list[str]:
        return [x.strip() for x in self.post_update.split("|") if x.strip()]

    def platform_ok(self) -> bool:
        if not self.platforms:
            return True
        plats = [p.strip().lower() for p in self.platforms.split("|")]
        return OS_NAME in plats


def _make_synthetic_project(name: str, category: str, update_method: str) -> Project:
    """为包管理器中智能发现的 AI 包创建一个临时 Project（不在 CSV 中）"""
    return Project(
        name=name,
        category=category,
        git_url="",
        dir_signature="",
        website="",
        update_method=update_method,
        platforms="win|mac",
        brew_name="",
        winget_id="",
        pip_packages="",
        post_update="",
    )


# ===========================================================
@dataclass
class Detection:
    """一次检测结果"""
    project: Project
    current_version: str
    latest_version: str = ""
    update_available: bool = False
    detected_by: str = ""        # dir | pip | brew | winget | choco | conda
    detected_path: str = ""      # 实际路径 或 包名
    status: str = "unknown"      # updatable / latest / error / manual


# ===========================================================
#  1. 加载配置
# ===========================================================

def load_projects() -> list[Project]:
    """从 projects.csv 加载所有项目"""
    projects = []
    if not PROJECTS_CSV.exists():
        print(f"{Fore.RED}x 找不到 {PROJECTS_CSV}，请确保 projects.csv 存在。")
        return projects

    with open(PROJECTS_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            p = Project(
                name=row.get("name", "").strip(),
                category=row.get("category", "").strip(),
                git_url=row.get("git_url", "").strip(),
                dir_signature=row.get("dir_signature", "").strip(),
                website=row.get("website", "").strip(),
                update_method=row.get("update_method", "").strip(),
                platforms=row.get("platforms", "").strip(),
                brew_name=row.get("brew_name", "").strip(),
                winget_id=row.get("winget_id", "").strip(),
                pip_packages=row.get("pip_packages", "").strip(),
                post_update=row.get("post_update", "").strip(),
            )
            if p.name:
                projects.append(p)
    return projects


def load_config(config_path: Optional[str] = None) -> dict:
    """加载 config.yaml，不存在则生成默认"""
    if config_path:
        cfg_path = Path(config_path)
    else:
        cfg_path = CONFIG_YAML
        if not cfg_path.exists():
            cfg_path = Path(DEFAULT_CONFIG_YAML)

    default_config = {
        "scan_paths": {
            "windows": ["D:\\AI", "D:\\AIwkspace",
                        "%USERPROFILE%\\source\\repos",
                        "%USERPROFILE%\\Desktop", "%USERPROFILE%\\Documents",
                        "%USERPROFILE%\\Downloads"],
            "mac": ["~/Desktop", "~/Documents", "~/Projects",
                    "~/dev", "~/Downloads", "~/Applications"],
        },
        "package_managers": {
            "pip": True, "npm": True, "brew": True,
            "winget": True, "choco": False, "conda": True,
        },
        "ignore_projects": [],
        "settings": {
            "auto_update": False,
            "parallel_updates": False,
            "fetch_timeout": 30,
            "show_scanned_dirs": True,
            "color_output": True,
        },
    }

    if yaml is None:
        print(f"{Fore.YELLOW}⚠ 未安装 pyyaml，使用默认配置（pip install pyyaml 以启用 config.yaml）")
        return default_config

    if not cfg_path.exists():
        _write_default_config(cfg_path, default_config)
        print(f"{Fore.GREEN}v 已生成默认配置 -> {cfg_path}")
        return default_config

    try:
        with open(cfg_path, encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"{Fore.YELLOW}⚠ 配置文件读取失败: {e}，使用默认配置")
        return default_config

    # 深度合并
    merged = _deep_merge(default_config, user_config)
    return merged


def _write_default_config(path: Path, config: dict):
    if yaml is None:
        return
    from copy import deepcopy
    cfg = deepcopy(config)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并 override 到 base"""
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def resolve_paths(paths: list[str]) -> list[Path]:
    """展开路径中的环境变量和 ~"""
    resolved = []
    for p in paths:
        p = os.path.expandvars(p)
        p = os.path.expanduser(p)
        resolved.append(Path(p))
    return resolved


# ===========================================================
#  2. 目录扫描 -- 检测 Git 项目和特征文件
# ===========================================================

def scan_directories(config: dict, projects: list[Project]) -> dict[str, Detection]:
    """扫描路径中的 Git 项目 + 特征文件，返回 {unique_key: Detection}"""
    detections: dict[str, Detection] = {}
    platform_key = "windows" if IS_WIN else "mac"
    scan_paths = resolve_paths(config.get("scan_paths", {}).get(platform_key, []))
    show_dirs = config.get("settings", {}).get("show_scanned_dirs", True)

    if show_dirs:
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}[扫描] 目录扫描 ({'Windows' if IS_WIN else 'macOS'})")
        print(f"{Fore.CYAN}{'='*60}")

    visited = set()

    for base_path in scan_paths:
        if not base_path.exists():
            if show_dirs:
                print(f"  {Fore.YELLOW}x 路径不存在: {base_path}")
            continue

        if show_dirs:
            print(f"  {Fore.WHITE}-> {base_path}")

        try:
            entries = list(base_path.iterdir())
        except PermissionError:
            if show_dirs:
                print(f"    {Fore.YELLOW}⚠ 无权限访问")
            continue

        for entry in sorted(entries):
            if not entry.is_dir():
                continue
            if entry.name in visited:
                continue

            git_dir = entry / ".git"
            if git_dir.is_dir():
                visited.add(entry.name)
                det = _identify_git_project(entry, projects)
                if det:
                    key = f"git:{det.project.name}:{entry}"
                    if key not in detections:
                        detections[key] = det
                        print(f"    {Fore.GREEN}v {det.project.name}  ({det.current_version})  [{entry}]")
            else:
                # 检测特征文件
                det = _identify_by_signature(entry, projects)
                if det:
                    key = f"sig:{det.project.name}:{entry}"
                    if key not in detections:
                        detections[key] = det
                        print(f"    {Fore.GREEN}v {det.project.name}  ({det.current_version})  [{entry}] -- 特征检测")

    return detections


def _identify_git_project(repo_path: Path, projects: list[Project]) -> Optional[Detection]:
    """根据 git remote URL 匹配项目"""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=str(repo_path),
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None
        remotes = result.stdout.lower()
    except Exception:
        return None

    for p in projects:
        if not p.platform_ok():
            continue
        if p.update_method not in ("git_pull", ""):
            continue
        for url_keyword in p.git_urls():
            if url_keyword.lower() in remotes:
                version = _git_current_version(repo_path)
                return Detection(
                    project=p,
                    current_version=version,
                    detected_by="dir",
                    detected_path=str(repo_path),
                    status="updatable" if version else "unknown",
                )
    return None


def _identify_by_signature(entry: Path, projects: list[Project]) -> Optional[Detection]:
    """根据特征文件/目录匹配项目"""
    for p in projects:
        if not p.platform_ok():
            continue
        sigs = p.dir_sigs()
        if not sigs:
            continue
        for sig in sigs:
            # 支持子目录 + 文件组合: "ComfyUI/main.py"
            sig_path = entry / sig
            if sig_path.exists():
                version = _git_current_version(entry) if (entry / ".git").is_dir() else _guess_version(entry, p)
                return Detection(
                    project=p,
                    current_version=version,
                    detected_by="dir",
                    detected_path=str(entry),
                    status="updatable" if version else "unknown",
                )
    return None


def _git_current_version(repo_path: Path) -> str:
    """获取当前 HEAD 短 hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_path),
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def _guess_version(entry: Path, project: Project) -> str:
    """尝试从各种文件推理版本号"""
    # 检查 version.txt / VERSION 等
    for candidate in ["version.txt", "VERSION", "version", "pyproject.toml", "setup.py", "setup.cfg"]:
        f = entry / candidate
        if f.is_file():
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if candidate == "pyproject.toml":
                    m = re.search(r'version\s*=\s*"(.*?)"', content)
                    if m:
                        return m.group(1)
                else:
                    first_line = content.strip().splitlines()[0]
                    return first_line[:80]
            except Exception:
                pass
    return ""


# ===========================================================
#  3. 包管理器扫描
# ===========================================================

def scan_package_managers(config: dict, projects: list[Project]) -> dict[str, Detection]:
    """依次扫描启用的包管理器（预设匹配 + 智能发现）"""
    detections: dict[str, Detection] = {}
    enabled = config.get("package_managers", {})

    if enabled.get("pip", True):
        print(f"\n{Fore.CYAN}[扫描] pip (Python)")
        print(f"  {Fore.WHITE}-- 预设项目匹配 --")
        _scan_pip(projects, detections)
        print(f"  {Fore.WHITE}-- 智能发现 --")
        _discover_pip(detections)

    if enabled.get("npm", True):
        print(f"\n{Fore.CYAN}[扫描] npm (Node.js)")
        print(f"  {Fore.WHITE}-- 预设项目匹配 --")
        _scan_npm(projects, detections)
        print(f"  {Fore.WHITE}-- 智能发现 --")
        _discover_npm(detections)

    if IS_MAC and enabled.get("brew", True):
        print(f"\n{Fore.CYAN}[扫描] Homebrew")
        print(f"  {Fore.WHITE}-- 预设项目匹配 --")
        _scan_brew(projects, detections)
        print(f"  {Fore.WHITE}-- 智能发现 --")
        _discover_brew(detections)

    if IS_WIN and enabled.get("winget", True):
        print(f"\n{Fore.CYAN}[扫描] winget (Windows)")
        print(f"  {Fore.WHITE}-- 预设项目匹配 --")
        _scan_winget(projects, detections)
        print(f"  {Fore.WHITE}-- 智能发现 --")
        _discover_winget(detections)

    if IS_WIN and enabled.get("choco", False):
        print(f"\n{Fore.CYAN}[扫描] Chocolatey")
        _scan_choco(projects, detections)

    if enabled.get("conda", True):
        _has_conda = shutil.which("conda")
        if _has_conda:
            print(f"\n{Fore.CYAN}[扫描] conda")
            print(f"  {Fore.WHITE}-- 预设项目匹配 --")
            _scan_conda(projects, detections)
            print(f"  {Fore.WHITE}-- 智能发现 --")
            _discover_conda(detections)

    return detections


def _scan_pip(projects: list[Project], detections: dict[str, Detection]):
    """pip list 匹配项目"""
    pip_pkgs = _get_pip_list()
    if not pip_pkgs:
        print("  pip 未找到或执行失败")
        return

    for p in projects:
        if not p.platform_ok():
            continue
        if p.update_method == "pip_upgrade":
            for pkg_candidate in p.pip_pkgs():
                for installed in pip_pkgs:
                    # pip 包名可能有连字符 vs 下划线差异，统一为小写比较
                    if installed["name"].lower().replace("-", "_") == pkg_candidate.lower().replace("-", "_"):
                        latest = _pypi_latest(installed["name"])
                        det = Detection(
                            project=p,
                            current_version=installed["version"],
                            latest_version=latest,
                            update_available=_version_newer(latest, installed["version"]),
                            detected_by="pip",
                            detected_path=installed["name"],
                            status="updatable" if _version_newer(latest, installed["version"]) else "latest",
                        )
                        key = f"pip:{p.name}:{installed['name']}"
                        if key not in detections:
                            detections[key] = det
                            icon = "v" if det.update_available else "="
                            print(f"  {Fore.GREEN}{icon} {p.name} ({installed['version']})  {'-> ' + latest if latest else ''}")


def _get_pip_list() -> list[dict]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return []


def _pypi_latest(package_name: str) -> str:
    try:
        import requests
        resp = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
        if resp.status_code == 200:
            return resp.json().get("info", {}).get("version", "")
    except Exception:
        pass
    return ""


def _scan_npm(projects: list[Project], detections: dict[str, Detection]):
    npm_global = _get_npm_global_list()
    if not npm_global:
        print("  npm 未找到或执行失败")
        return
    for p in projects:
        if not p.platform_ok():
            continue
        if p.pip_packages:  # npm 项目暂时用 pip_packages 列存关联包（可后续扩展独立列）
            for installed_name, installed_ver in npm_global.items():
                pkg_lower = installed_name.lower()
                for pp in p.pip_pkgs():
                    if pp.lower() in pkg_lower:
                        print(f"  {Fore.GREEN}v {p.name} ({installed_ver}) -- npm global")
                        det = Detection(
                            project=p, current_version=installed_ver,
                            detected_by="npm", detected_path=installed_name,
                            status="updatable",
                        )
                        key = f"npm:{p.name}:{installed_name}"
                        if key not in detections:
                            detections[key] = det


def _get_npm_global_list() -> dict[str, str]:
    """返回 {package_name: version}"""
    try:
        npm = "npm.cmd" if IS_WIN else "npm"
        result = subprocess.run(
            [npm, "list", "-g", "--depth=0", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            deps = data.get("dependencies", {})
            return {k: v.get("version", "") for k, v in deps.items()}
    except Exception:
        pass
    return {}


def _scan_brew(projects: list[Project], detections: dict[str, Detection]):
    brew_list = _get_brew_list()
    if not brew_list:
        return

    for p in projects:
        if not p.platform_ok() or not p.brew_name:
            continue
        for name, info in brew_list.items():
            if name.lower() == p.brew_name.lower():
                current_ver = info.get("installed_version", "")
                latest_ver = info.get("latest_version", "")
                det = Detection(
                    project=p, current_version=current_ver, latest_version=latest_ver,
                    update_available=_version_newer(latest_ver, current_ver),
                    detected_by="brew", detected_path=name,
                    status="updatable" if _version_newer(latest_ver, current_ver) else "latest",
                )
                key = f"brew:{p.name}:{name}"
                if key not in detections:
                    detections[key] = det
                    icon = "v" if det.update_available else "="
                    print(f"  {Fore.GREEN}{icon} {p.name} ({current_ver})  -> {latest_ver}")


def _get_brew_list() -> dict[str, dict]:
    try:
        result = subprocess.run(
            ["brew", "info", "--json=v2", "--installed"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            pkgs = {}
            for cat_key in ("formulae", "casks"):
                for item in data.get(cat_key, []):
                    name = item.get("name", "")
                    versions_info = item.get("versions", {})
                    pkgs[name] = {
                        "installed_version": versions_info.get("stable", ""),
                        "latest_version": versions_info.get("stable", ""),
                        "type": cat_key,
                    }
            return pkgs
    except Exception:
        pass
    return {}


def _scan_winget(projects: list[Project], detections: dict[str, Detection]):
    winget_list = _get_winget_list()
    if not winget_list:
        print("  winget 未找到或执行失败")
        return

    for p in projects:
        if not p.platform_ok() or not p.winget_id:
            continue
        for installed_id, info in winget_list.items():
            if installed_id.lower() == p.winget_id.lower():
                current_ver = info.get("version", "")
                det = Detection(
                    project=p, current_version=current_ver,
                    detected_by="winget", detected_path=installed_id,
                    status="updatable",
                )
                key = f"winget:{p.name}:{installed_id}"
                if key not in detections:
                    detections[key] = det
                    print(f"  {Fore.GREEN}v {p.name} ({current_ver})")


def _get_winget_list() -> dict[str, dict]:
    try:
        result = subprocess.run(
            ["winget", "list", "--accept-source-agreements"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            output = result.stdout
            pkgs = {}
            # 用正则解析 winget 的输出（表格式）
            for line in output.splitlines():
                m = re.match(r'^(\S[\S ]*?)\s{2,}(\S+)\s{2,}(\S+)', line)
                if m and "Name" not in m.group(1):
                    name = m.group(1).strip()
                    pkg_id = m.group(2).strip()
                    version = m.group(3).strip()
                    pkgs[pkg_id] = {"name": name, "version": version}
            return pkgs
    except Exception:
        pass
    return {}


def _scan_choco(projects: list[Project], detections: dict[str, Detection]):
    print("  Chocolatey 扫描暂未实现")


def _scan_conda(projects: list[Project], detections: dict[str, Detection]):
    conda_list = _get_conda_list()
    if not conda_list:
        return

    AI_CONDA_PKGS = {
        "pytorch", "torch", "torchvision", "torchaudio",
        "transformers", "datasets", "accelerate", "diffusers",
        "langchain", "langchain-core", "llama-index-core",
        "chromadb", "qdrant-client", "pymilvus", "faiss",
        "gradio", "openai", "sentence-transformers",
    }

    for pkg_name, version in conda_list.items():
        if pkg_name.lower() in AI_CONDA_PKGS:
            for p in projects:
                for pp in p.pip_pkgs():
                    if pp.lower().replace("-", "_") == pkg_name.lower().replace("-", "_"):
                        print(f"  {Fore.GREEN}v {p.name} ({version}) -- conda")
                        det = Detection(
                            project=p, current_version=version,
                            detected_by="conda", detected_path=pkg_name,
                            status="updatable",
                        )
                        key = f"conda:{p.name}:{pkg_name}"
                        if key not in detections:
                            detections[key] = det


def _get_conda_list() -> dict[str, str]:
    try:
        result = subprocess.run(
            ["conda", "list", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {item.get("name", ""): item.get("version", "") for item in data}
    except Exception:
        pass
    return {}


# -- 智能发现 ---- 扫描全部已装包，抓出 AI 相关的（不限 CSV 预设）----

def _discover_pip(detections: dict[str, Detection]):
    pip_pkgs = _get_pip_list()
    if not pip_pkgs:
        return
    found = 0
    for installed in pip_pkgs:
        name = installed["name"]
        if not _is_ai_package(name):
            continue
        key = f"pip:discovered:{name}"
        if key in detections:
            continue
        version = installed["version"]
        latest = _pypi_latest(name)
        updatable = _version_newer(latest, version)
        sp = _make_synthetic_project(name, "discovered", "pip_upgrade")
        sp.pip_packages = name
        detections[key] = Detection(
            project=sp, current_version=version, latest_version=latest,
            update_available=updatable, detected_by="pip",
            detected_path=name,
            status="updatable" if updatable else "latest",
        )
        icon = "!" if updatable else "-"
        print(f"  {Fore.MAGENTA}{icon} [发现] {name} ({version})  {'-> ' + latest if latest else ''}")
        found += 1
    if found:
        print(f"  {Fore.MAGENTA}  pip 智能发现 {found} 个 AI 相关包")


def _discover_npm(detections: dict[str, Detection]):
    npm_pkgs = _get_npm_global_list()
    if not npm_pkgs:
        return
    found = 0
    for name, version in npm_pkgs.items():
        if not _is_ai_package(name):
            continue
        key = f"npm:discovered:{name}"
        if key in detections:
            continue
        sp = _make_synthetic_project(name, "discovered", "manual")
        detections[key] = Detection(
            project=sp, current_version=version, detected_by="npm",
            detected_path=name, status="updatable",
        )
        print(f"  {Fore.MAGENTA}- [发现] {name} ({version})  -- npm global")
        found += 1
    if found:
        print(f"  {Fore.MAGENTA}  npm 智能发现 {found} 个 AI 相关包")


def _discover_brew(detections: dict[str, Detection]):
    brew_list = _get_brew_list()
    if not brew_list:
        return
    found = 0
    for name, info in brew_list.items():
        ai_brew_keywords = {"ollama", "comfyui", "diffusion", "whisper", "llama",
                            "chatgpt", "copilot", "stable-diffusion", "lm-studio",
                            "jupyter", "tensorflow", "pytorch", "huggingface"}
        if not _is_ai_package(name):
            matched = False
            for kw in ai_brew_keywords:
                if kw in name.lower():
                    matched = True
                    break
            if not matched:
                continue
        key = f"brew:discovered:{name}"
        if key in detections:
            continue
        current_ver = info.get("installed_version", "")
        latest_ver = info.get("latest_version", "")
        updatable = _version_newer(latest_ver, current_ver)
        sp = _make_synthetic_project(name, "discovered", "brew_upgrade")
        sp.brew_name = name
        detections[key] = Detection(
            project=sp, current_version=current_ver, latest_version=latest_ver,
            update_available=updatable, detected_by="brew",
            detected_path=name,
            status="updatable" if updatable else "latest",
        )
        icon = "!" if updatable else "-"
        print(f"  {Fore.MAGENTA}{icon} [发现] {name} ({current_ver})  -> {latest_ver}")
        found += 1
    if found:
        print(f"  {Fore.MAGENTA}  brew 智能发现 {found} 个 AI 相关包")


def _discover_winget(detections: dict[str, Detection]):
    winget_list = _get_winget_list()
    if not winget_list:
        return
    found = 0
    for installed_id, info in winget_list.items():
        name = info.get("name", installed_id)
        if not _is_ai_package(name) and not _is_ai_package(installed_id):
            continue
        key = f"winget:discovered:{installed_id}"
        if key in detections:
            continue
        sp = _make_synthetic_project(name, "discovered", "winget_upgrade")
        sp.winget_id = installed_id
        detections[key] = Detection(
            project=sp, current_version=info.get("version", ""),
            detected_by="winget", detected_path=installed_id,
            status="updatable",
        )
        print(f"  {Fore.MAGENTA}- [发现] {name} ({info.get('version', '')})")
        found += 1
    if found:
        print(f"  {Fore.MAGENTA}  winget 智能发现 {found} 个 AI 相关包")


def _discover_conda(detections: dict[str, Detection]):
    conda_list = _get_conda_list()
    if not conda_list:
        return
    found = 0
    for name, version in conda_list.items():
        if not _is_ai_package(name):
            continue
        key = f"conda:discovered:{name}"
        if key in detections:
            continue
        sp = _make_synthetic_project(name, "discovered", "manual")
        detections[key] = Detection(
            project=sp, current_version=version, detected_by="conda",
            detected_path=name, status="updatable",
        )
        print(f"  {Fore.MAGENTA}- [发现] {name} ({version})  -- conda")
        found += 1
    if found:
        print(f"  {Fore.MAGENTA}  conda 智能发现 {found} 个 AI 相关包")


# ==============================================================
#  4. 版本比对
# ==============================================================

def _version_newer(latest: str, current: str) -> bool:
    """判断 latest 是否比 current 新。无法比较时返回 False"""
    if not latest or not current:
        return False
    if latest == current:
        return False
    try:
        from packaging.version import parse
        return parse(latest) > parse(current)
    except Exception:
        # fallback: 字符串直接比较
        return latest != current


def check_git_updates(detections: dict[str, Detection]):
    """对 git 项目检测是否有新提交"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}[检查] Git 项目更新状态...")
    print(f"{Fore.CYAN}{'='*60}")

    for key, det in detections.items():
        if det.detected_by != "dir":
            continue
        repo_path = Path(det.detected_path)
        if not (repo_path / ".git").is_dir():
            continue

        try:
            # git fetch --dry-run
            subprocess.run(
                ["git", "fetch", "--dry-run"],
                cwd=str(repo_path),
                capture_output=True, text=True, timeout=15,
            )
            # 对比 origin/main 或 origin/master
            behind = _git_behind_count(repo_path)
            if behind is not None and behind > 0:
                det.update_available = True
                det.status = "updatable"
                det.latest_version = _git_remote_head(repo_path)
                print(f"  {Fore.YELLOW}~ {det.project.name}: 落后 {behind} 个 commit  -> {det.latest_version}")
            else:
                det.update_available = False
                det.status = "latest"
                print(f"  {Fore.GREEN}v {det.project.name}: 已是最新")
        except Exception as e:
            det.status = "error"
            print(f"  {Fore.RED}x {det.project.name}: fetch 失败 ({e})")


def _git_behind_count(repo_path: Path) -> Optional[int]:
    """返回落后远程的 commit 数"""
    try:
        # 先尝试 origin/main
        for branch in ["origin/main", "origin/master"]:
            result = subprocess.run(
                ["git", "rev-list", "--count", f"HEAD..{branch}"],
                cwd=str(repo_path),
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
    except Exception:
        pass

    # fallback: 查看 git status
    try:
        result = subprocess.run(
            ["git", "status", "-uno"],
            cwd=str(repo_path),
            capture_output=True, text=True, timeout=10,
        )
        if "behind" in result.stdout:
            return 1  # 至少落后 1 个
    except Exception:
        pass

    return None


def _git_remote_head(repo_path: Path) -> str:
    try:
        for branch in ["origin/main", "origin/master"]:
            result = subprocess.run(
                ["git", "rev-parse", "--short", branch],
                cwd=str(repo_path),
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
    except Exception:
        pass
    return ""


# ==============================================================
#  5. 报告输出
# ==============================================================

def report(detections: dict[str, Detection]):
    """彩色表格输出检测结果"""
    dets = list(detections.values())
    if not dets:
        print(f"\n{Fore.YELLOW}未检测到任何 AI 项目。\n"
              f"提示：在 config.yaml 中调整 scan_paths，"
              f"或在 projects.csv 中添加自定义项目。")
        return

    # 分组
    preset = [d for d in dets if d.project.category != "discovered"]
    discovered = [d for d in dets if d.project.category == "discovered"]

    if preset:
        print(f"\n{Fore.CYAN}{'='*100}")
        print(f"{Fore.CYAN}{Fore.WHITE}[预设项目] 来自 projects.csv -- 共 {Fore.YELLOW}{len(preset)}{Fore.WHITE} 个")
        print(f"{Fore.CYAN}{'='*100}")
        _print_table(preset)

    if discovered:
        print(f"\n{Fore.MAGENTA}{'='*100}")
        print(f"{Fore.MAGENTA}{Fore.WHITE}[智能发现] 来自包管理器 AI 关键词匹配 -- 共 {Fore.YELLOW}{len(discovered)}{Fore.WHITE} 个")
        print(f"{Fore.MAGENTA}{'='*100}")
        _print_table(discovered)

    updatable_count = sum(1 for d in dets if d.status == "updatable")
    latest_count = len(dets) - updatable_count
    print(f"\n{Fore.WHITE}{'-'*60}")
    print(f"  {Fore.YELLOW}可更新: {updatable_count}   {Fore.GREEN}已最新: {latest_count}   {Fore.WHITE}总计: {len(dets)}")


def _print_table(dets: list[Detection]):
    """打印单个表格"""
    header = f"{'#':<4}{'项目':<32}{'当前版本':<18}{'最新版本':<18}{'来源':<12}{'状态'}"
    sep = "-" * 100
    print(Fore.WHITE + header)
    print(Fore.WHITE + sep)

    for i, d in enumerate(dets, 1):
        tag = "[预设]" if d.project.category != "discovered" else "[发现]"
        status_map = {
            "updatable": f"{Fore.YELLOW}可更新",
            "latest": f"{Fore.GREEN}已最新",
            "manual": f"{Fore.MAGENTA}手动",
            "error": f"{Fore.RED}错误",
        }
        status = status_map.get(d.status, d.status)

        name = d.project.name[:28]
        cur = d.current_version[:16]
        latest_ver = d.latest_version[:16] if d.latest_version else "-"

        print(f"{i:<4}{name:<32}{cur:<18}{latest_ver:<18}{d.detected_by:<12}{status}")


# ==============================================================
#  6. 交互式更新
# ==============================================================

def interactive_update(detections: dict[str, Detection], auto: bool = False):
    """交互式选择并执行更新"""
    updatable = {k: v for k, v in detections.items() if v.status == "updatable"}
    if not updatable:
        print(f"{Fore.GREEN}所有项目已是最新版本！")
        return

    dets = sorted(updatable.values(), key=lambda x: (x.project.category == "discovered", x.project.name))

    if auto:
        selected = list(range(len(dets)))
    else:
        n_preset = sum(1 for d in dets if d.project.category != "discovered")
        n_disc = len(dets) - n_preset

        print(f"\n{Fore.WHITE}{'='*50}")
        print(f"{Fore.WHITE}共 {Fore.YELLOW}{len(dets)}{Fore.WHITE} 个项目可更新")
        if n_preset:
            print(f"  {Fore.CYAN}[预设] {n_preset} 个（来自 projects.csv）")
        if n_disc:
            print(f"  {Fore.MAGENTA}[发现] {n_disc} 个（包管理器智能匹配）")
        print(f"{Fore.WHITE}{'='*50}")

        print(f"\n{Fore.WHITE}你想升级哪些？")
        print(f"  【1,3,5】 选序号    【1-5】 范围    【all】 全部    【p】 仅预设    【d】 仅发现    【q】 退出")
        choice = input(f"{Fore.CYAN}> ").strip()

        if choice.lower() == "q":
            print(f"{Fore.YELLOW}已取消。")
            return

        if choice.lower() == "all":
            selected = list(range(len(dets)))
        elif choice.lower() == "p":
            selected = [i for i, d in enumerate(dets) if d.project.category != "discovered"]
            if not selected:
                print(f"{Fore.YELLOW}没有预设项目可更新。")
                return
            print(f"  {Fore.CYAN}选中 {len(selected)} 个预设项目")
        elif choice.lower() == "d":
            selected = [i for i, d in enumerate(dets) if d.project.category == "discovered"]
            if not selected:
                print(f"{Fore.YELLOW}没有智能发现项目可更新。")
                return
            print(f"  {Fore.MAGENTA}选中 {len(selected)} 个智能发现项目")
        else:
            selected = _parse_selection(choice, len(dets))
            if not selected:
                print(f"{Fore.RED}无效的选择。")
                return

    if not selected:
        return

    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}[更新] 开始更新 {len(selected)} 个项目...")
    print(f"{Fore.MAGENTA}{'='*60}")

    success, failed, skipped = 0, 0, 0

    for idx in selected:
        det = dets[idx]
        print(f"\n  {Fore.WHITE}> {det.project.name} [{det.project.update_method}]")
        ok = _do_update(det)
        if ok is True:
            success += 1
            print(f"  {Fore.GREEN}  OK 成功")
        elif ok is False:
            failed += 1
            print(f"  {Fore.RED}  FAIL 失败")
        else:
            skipped += 1

    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}更新完成: {Fore.GREEN}OK {success} {Fore.RED}FAIL {failed} {Fore.WHITE}SKIP {skipped}")
    print(f"{Fore.CYAN}{'='*60}")


def _parse_selection(s: str, max_n: int) -> list[int]:
    """解析用户输入 '1,3,5-7' -> [0, 2, 4, 5, 6]"""
    indices = set()
    parts = re.split(r'[,;，；\s]+', s)
    for part in parts:
        part = part.strip()
        if re.match(r'^\d+-\d+$', part):
            lo, hi = part.split("-")
            for i in range(int(lo), int(hi) + 1):
                if 1 <= i <= max_n:
                    indices.add(i - 1)
        elif part.isdigit():
            i = int(part)
            if 1 <= i <= max_n:
                indices.add(i - 1)
    return sorted(indices)


def _do_update(det: Detection) -> Optional[bool]:
    """执行单个项目的更新。返回 True/False/None(跳过)"""
    method = det.project.update_method

    if method == "git_pull":
        return _update_git(det)
    elif method == "pip_upgrade":
        return _update_pip(det)
    elif method == "brew_upgrade":
        return _update_brew(det)
    elif method == "winget_upgrade":
        return _update_winget(det)
    elif method == "manual":
        print(f"  {Fore.YELLOW}  LINK 请手动更新: {det.project.website}")
        return None
    else:
        print(f"  {Fore.YELLOW}  未知更新方式: {method}")
        return None


def _update_git(det: Detection) -> bool:
    repo_path = Path(det.detected_path)
    if not (repo_path / ".git").is_dir():
        print(f"  {Fore.RED}  不是 git 仓库: {repo_path}")
        return False

    # 1. stash 保护本地修改
    stash = False
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_path),
            capture_output=True, text=True, timeout=10,
        )
        if status.stdout.strip():
            print(f"  {Fore.YELLOW}  检测到本地修改，暂存中...")
            subprocess.run(["git", "stash"], cwd=str(repo_path), capture_output=True, timeout=10)
            stash = True
    except Exception:
        pass

    # 2. pull
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=str(repo_path),
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            print(f"  {Fore.RED}  git pull 失败: {result.stderr.strip()[:200]}")
            return False
    except Exception as e:
        print(f"  {Fore.RED}  git pull 异常: {e}")
        return False

    # 3. post_update 命令
    for cmd in det.project.post_cmds():
        print(f"  {Fore.WHITE}  执行: {cmd}")
        try:
            subprocess.run(
                shlex.split(cmd) if IS_WIN else cmd.split(),
                cwd=str(repo_path),
                capture_output=True, text=True, timeout=300,
            )
        except Exception as e:
            print(f"  {Fore.YELLOW}  命令未完成: {e}")

    return True


def _update_pip(det: Detection) -> bool:
    pkgs = det.project.pip_pkgs()
    if not pkgs:
        pkgs = [det.detected_path]
    for pkg in pkgs:
        print(f"  {Fore.WHITE}  pip install --upgrade {pkg}")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode != 0:
                print(f"  {Fore.RED}  pip 失败: {result.stderr.strip()[:200]}")
                return False
        except Exception as e:
            print(f"  {Fore.RED}  pip 异常: {e}")
            return False
    return True


def _update_brew(det: Detection) -> bool:
    name = det.project.brew_name or det.detected_path
    print(f"  {Fore.WHITE}  brew upgrade {name}")
    try:
        result = subprocess.run(
            ["brew", "upgrade", name],
            capture_output=True, text=True, timeout=600,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  {Fore.RED}  brew 异常: {e}")
        return False


def _update_winget(det: Detection) -> bool:
    winget_id = det.project.winget_id or det.detected_path
    print(f"  {Fore.WHITE}  winget upgrade {winget_id}")
    try:
        result = subprocess.run(
            ["winget", "upgrade", winget_id, "--accept-source-agreements"],
            capture_output=True, text=True, timeout=600,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  {Fore.RED}  winget 异常: {e}")
        return False


# ===========================================================
#  7. 主流程
# ===========================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI Updater -- 一键检测并更新 AI 开源项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ai_updater.py                 扫描 + 交互更新
  python ai_updater.py --scan-only     只扫描
  python ai_updater.py --update-all    自动全部更新
  python ai_updater.py --config my.yaml  指定配置
        """,
    )
    parser.add_argument("--scan-only", action="store_true", help="只扫描不更新")
    parser.add_argument("--update-all", action="store_true", help="扫描后自动更新全部")
    parser.add_argument("--config", type=str, default=None, help="指定配置文件路径")
    args = parser.parse_args()

    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}| {Fore.WHITE}AI Updater  --  一键更新你的 AI 开源工具箱")
    print(f"{Fore.CYAN}|{'='*58}{'|'}")
    label = {"windows": "Windows 模式", "darwin": "macOS 模式"}.get(OS_NAME, f"{OS_NAME} 模式")
    print(f"{Fore.CYAN}|  {Fore.YELLOW}{label}{' ' * (52 - len(label))}{Fore.CYAN}|")
    print(f"{Fore.CYAN}|{'='*58}{'|'}")
    print(f"{Fore.CYAN}|  {Fore.WHITE}编辑 projects.csv 添加自定义项目{' ' * 27}{Fore.CYAN}|")
    print(f"{Fore.CYAN}|  {Fore.WHITE}编辑 config.yaml  调整扫描路径{' ' * 30}{Fore.CYAN}|")
    print(f"{Fore.CYAN}{'='*60}")

    # 加载
    config = load_config(args.config)
    projects = load_projects()
    if not projects:
        print(f"{Fore.RED}x 未能加载任何项目，请检查 {PROJECTS_CSV}")
        sys.exit(1)

    print(f"{Fore.WHITE}已加载 {Fore.GREEN}{len(projects)}{Fore.WHITE} 个预设项目（projects.csv）")

    # 扫描
    detections = scan_directories(config, projects)
    detections.update(scan_package_managers(config, projects))

    # 过滤忽略项目
    ignore_list = config.get("ignore_projects") or []
    detections = {k: v for k, v in detections.items() if v.project.name not in ignore_list}

    # 检测 git 更新
    check_git_updates(detections)

    # 汇总统计
    n_preset = sum(1 for d in detections.values() if d.project.category != "discovered")
    n_disc = len(detections) - n_preset
    if n_disc > 0:
        print(f"\n{Fore.MAGENTA}[汇总] 预设 {n_preset} + 智能发现 {n_disc} = 共 {len(detections)} 个项目")

    # 报告
    report(detections)

    if args.scan_only:
        print(f"\n{Fore.CYAN}扫描完成（--scan-only）。")
        return

    # 更新
    interactive_update(detections, auto=args.update_all or config.get("settings", {}).get("auto_update", False))


if __name__ == "__main__":
    main()
