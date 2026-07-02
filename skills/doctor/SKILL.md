---
name: doctor
description: "环境检查与安装向导。检查 MathModelAgent V2.6 工作流所需依赖是否已安装，对缺失项提供安装命令，并在用户确认后执行安装。手动触发。"
allowed-tools: Bash(*), Read, Write
---

# Doctor 环境检查与安装向导

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 独立工具，不参与工作流阶段调度 · 共享规范: [[skills/_references/SKILL|_references]]

本 skill 检查 MathModelAgent V2.6 工作流所需工具是否已就绪，并帮助用户安装缺失项。只在用户显式触发时运行，不自动执行。

## 检查项清单

### 核心工具

| 工具 | 用途 | 检测命令 |
| --- | --- | --- |
| `typst` | Typst 论文编译 | `command -v typst` |
| `xelatex` | LaTeX 论文编译，中文模板常用 | `command -v xelatex` |
| `python3` / `python` | 数值计算、RAG、审计脚本 | `command -v python3` 或 `command -v python` |
| `drawio` / `draw.io` | 流程图导出，选装 | `command -v drawio` 或 `command -v draw.io` |
| `pdftoppm` | PDF 视觉检查，选装 | `command -v pdftoppm` |
| `mutool` | PDF 视觉检查备用，选装 | `command -v mutool` |
| `magick` | PDF/图像处理备用，选装 | `command -v magick` |

### Python 包

| 包 | 用途 |
| --- | --- |
| `numpy` | 数值计算 |
| `scipy` | 科学计算、优化求解 |
| `pandas` | 数据处理 |
| `matplotlib` | 图表生成 |
| `scikit-learn` | 机器学习建模 |
| `openpyxl` | 读写 Excel 数据附件 |
| `chromadb` | 本地 RAG 向量库，选装 |
| `sentence-transformers` | 本地 embedding，选装 |

### 科研绘图增强，选装

| 项 | 用途 | 检测命令 |
| --- | --- | --- |
| `nature-figure` | 可选接入 `Yuan1z0825/nature-skills`，增强论文级科研绘图 | `python skills/_references/scripts/resolve_nature_figure.py --workspace <workspace>` |
| `audit_v2_run.py` | V2 只读审计 PNG-only、Pillow 数据图、缺矢量包、短论文误 PASS 等问题 | `python skills/_references/scripts/audit_v2_run.py --workspace <workspace>` |
| `svglite` / `ragg` / `patchwork` | R 后端投稿级 SVG/PDF/TIFF 导出 | `Rscript -e "library(svglite); library(ragg); library(patchwork)"` |

## 工作流程

### Step 1: 检测当前平台

```bash
case "$(uname -s)" in
  Darwin) echo "PLATFORM=mac" ;;
  Linux)  echo "PLATFORM=linux" ;;
  MINGW*|MSYS*|CYGWIN*) echo "PLATFORM=windows" ;;
  *)      echo "PLATFORM=unknown" ;;
esac
```

Windows 下优先使用 winget，备用 scoop 或 choco。Linux 下优先使用 apt，备用 dnf 或 pacman。

### Step 2: 检查所有工具

```bash
check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "OK  $1 ($(command -v "$1"))"
  else
    echo "MISS $1"
  fi
}

check_cmd typst
check_cmd xelatex
check_cmd python3 || check_cmd python
command -v drawio >/dev/null 2>&1 || command -v draw.io >/dev/null 2>&1 \
  && echo "OK  drawio" || echo "MISS drawio"
check_cmd pdftoppm
check_cmd mutool
check_cmd magick
```

Check Python packages:

```bash
python3 - <<'PYEOF'
import importlib
import importlib.metadata as meta

pkgs = ["numpy", "scipy", "pandas", "matplotlib", "sklearn", "openpyxl", "chromadb", "sentence_transformers"]
for p in pkgs:
    try:
        importlib.import_module(p)
        dist = {"sklearn": "scikit-learn", "sentence_transformers": "sentence-transformers"}.get(p, p)
        try:
            ver = meta.version(dist)
        except Exception:
            ver = "?"
        print(f"OK  {p} ({ver})")
    except ImportError:
        print(f"MISS {p}")
PYEOF
```

Check optional Nature Figure:

```bash
python3 skills/_references/scripts/resolve_nature_figure.py --workspace . 2>/dev/null || \
python skills/_references/scripts/resolve_nature_figure.py --workspace . 2>/dev/null || true
```

### Step 3: 输出检查报告

整理成类似格式：

```text
状态   工具/包              说明
----   --------             ----
✓      typst 0.13.0         论文编译
✗      drawio               DrawIO 导出 PDF，选装
✓      python3 3.11.x       数值计算
✗      scipy                科学计算，选装
```

必须项：`typst` 或 `xelatex` 至少一个、Python、`numpy`、`pandas`、`matplotlib`。

可选项：`drawio`、PDF 转 PNG 工具、`scipy`、`scikit-learn`、`openpyxl`、RAG 依赖、Nature Figure、R 绘图包。

### Step 4: 提供安装命令

只对缺失项输出对应平台命令。

#### typst

| 平台 | 命令 |
| --- | --- |
| macOS | `brew install typst` |
| Linux | `snap install typst` 或从 GitHub Releases 下载二进制 |
| Arch | `pacman -S typst` |
| Windows winget | `winget install Typst.Typst` |
| Windows scoop | `scoop install typst` |
| 通用 | `cargo install --locked typst-cli` |

#### xelatex

xelatex 包含在主流 TeX 发行版中。

| 平台 | 命令 |
| --- | --- |
| macOS | `brew install --cask mactex` 或 `brew install texlive` |
| Linux apt | `sudo apt install texlive-full` |
| Linux dnf | `sudo dnf install texlive-scheme-full` |
| Arch | `sudo pacman -S texlive` |
| Windows | `winget install MiKTeX.MiKTeX` 或 `winget install TeXLive` |

#### Python 包

```bash
pip install numpy scipy pandas matplotlib scikit-learn openpyxl
pip install chromadb sentence-transformers
```

#### nature-figure，选装

```bash
git clone https://github.com/Yuan1z0825/nature-skills.git
export NATURE_SKILLS_ROOT="$(pwd)/nature-skills"
python skills/_references/scripts/resolve_nature_figure.py --workspace .
```

Windows PowerShell:

```powershell
$env:NATURE_SKILLS_ROOT = "C:\path\to\nature-skills"
python skills/_references/scripts/resolve_nature_figure.py --workspace .
```

R 后端按需安装：

```r
install.packages(c("ggplot2", "patchwork", "svglite", "ragg", "ggrepel"))
```

#### drawio

| 平台 | 命令 |
| --- | --- |
| macOS | `brew install --cask drawio` |
| Linux | 从 drawio-desktop Releases 下载 AppImage 或 deb |
| Windows | `winget install JGraph.Draw` |

#### PDF 工具

```bash
# macOS
brew install poppler mupdf imagemagick

# Debian/Ubuntu
sudo apt install poppler-utils mupdf-tools imagemagick

# Windows
winget install oschwartz10612.poppler
winget install ImageMagick.ImageMagick
```

### Step 5: 询问用户是否安装

列出所有缺失的必须项后，询问用户：

```text
以上必须项缺失，是否现在安装？(y/N)
```

- 若用户确认，按检测到的平台依次执行安装命令，每步完成后打印结果。
- 若用户拒绝或只有可选项缺失，打印可手动执行的命令列表并退出。
- 安装完成后重新运行 Step 2，确认已生效。

### Step 6: 最终摘要

```text
Doctor 检查完成
必须项：5/5 ✓
可选项：2/4，drawio、scipy 缺失

工作流就绪状态：
  mm-start-contest-v2  ✓
  论文编译              ✓
  数据图表              ✓
  Control Center        ✓
  nature-figure         可选
```

注：V1 工作流已归档，不再单独列出其状态。

## 注意事项

- 执行安装前必须获得用户明确确认，不得静默安装。
- Windows 下建议在 PowerShell 管理员模式或 Git Bash 中运行，部分命令需要管理员权限。
- Linux 的 `sudo` 命令会请求密码，执行前告知用户。
- drawio 和 PDF 转 PNG 工具缺失不影响核心工作流，仅影响导出质量。
- 如平台检测为 unknown，打印所有平台命令供用户手动选择。
