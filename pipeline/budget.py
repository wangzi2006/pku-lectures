from __future__ import annotations

import os

from common import read_json

usage = read_json("usage.json", {})
estimated = float(usage.get("estimatedCny", 0))
soft = float(os.getenv("AI_SOFT_BUDGET_CNY", "35"))
hard = float(os.getenv("AI_HARD_BUDGET_CNY", "45"))
status = "hard" if estimated >= hard else "soft" if estimated >= soft else "ok"

print(f"status={status}")
print(f"estimated_cny={estimated:.2f}")
