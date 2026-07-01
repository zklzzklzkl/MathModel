---
library: code_templates
year: 2026
contest: generic
problem_id: python-validation-demo
tags: [python, validation, baseline, reproducibility]
license: project-authored
---

# Python 验证模板样例

适用场景：任何预测、评价、优化或仿真模型都需要一个可复现的基准和验证脚本。

模板要点：

```python
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "code" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(2026)

def save_metric(name, value, unit="", description=""):
    row = {"id": name, "value": float(value), "unit": unit, "description": description}
    (OUT / f"{name}.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
```

最低要求：

- 固定随机种子。
- 保存中间结果和指标 JSON/CSV。
- 至少实现一个简单 baseline。
- 将图表和指标写入 `RESULTS_MANIFEST.json`。

风险提示：模板只能提供代码骨架，变量名、指标和验证方式必须来自当前题面与建模决策。
