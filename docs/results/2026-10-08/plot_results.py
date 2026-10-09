"""Render the saved Luna/Sol scores; run from any directory."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "yugioh-sol-luna-20261008"
import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).resolve().parent
luna = json.loads((root / "luna.score.json").read_text(encoding='utf-8'))
sol = json.loads((root / "sol.score.json").read_text(encoding='utf-8'))
keys = ["state_recreation", "human_move_agreement", "rule_correctness"]
labels = ["State recreation", "Human move reproduction", "Rules correctness", "Final score · equal weights"]
fig, ax = plt.subplots(figsize=(10, 5.1))
fig.patch.set_facecolor("#ffffff")
y = np.arange(4)
for report, offset, color, label in [
    (sol, -0.18, "#2563eb", "GPT-6.1 Sol"),
    (luna, 0.18, "#d97706", "GPT-6 Luna"),
]:
    values = [100 * report["kpis"][k]["score"] for k in keys] + [report["final_score_percent"]]
    bars = ax.barh(y + offset, values, height=0.30, color=color, label=label)
    for i, (bar, value) in enumerate(zip(bars, values)):
        tally = report["kpis"][keys[i]] if i < 3 else None
        text = f"{value:.2f}%" + (f"  ({tally['passed']}/{tally['total']})" if tally else "")
        ax.text(value + 1.1, bar.get_y() + bar.get_height()/2, text,
                va="center", fontsize=10, color="#1f2937")

ax.set_yticks(y, labels, fontsize=11)
ax.invert_yaxis()
ax.set_xlim(0, 117)
ax.set_xticks(range(0, 101, 20), [f"{i}%" for i in range(0, 101, 20)])
ax.set_xlabel("Score", color="#4b5563", fontsize=10)
ax.set_axisbelow(True)
ax.grid(axis="x", color="#e5e7eb", linewidth=0.8)
ax.axhline(2.5, color="#d1d5db", linewidth=0.8)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.tick_params(length=0, pad=8, colors="#4b5563")
fig.suptitle("Replay benchmark · Sol and Luna", x=0.03, ha="left",
             fontsize=17, fontweight="bold", color="#111827")
fig.text(0.03, 0.89, "18 reviewed positions · 36 tasks per model · Duelingbook replay 40753-85958923",
         fontsize=10, color="#4b5563")
ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.19), frameon=False, ncol=2, fontsize=10)
fig.text(0.03, 0.035, "Assisted checkpoint pilot; prompts differed. Not a continuous duel or a controlled model ranking.",
         fontsize=9, color="#4b5563")
fig.subplots_adjust(left=0.28, right=0.97, top=0.80, bottom=0.15)
fig.savefig(root / "kpi-comparison.png", dpi=180, facecolor="white")
fig.savefig(root / "kpi-comparison.svg", facecolor="white", metadata={"Date": None})
svg = root / "kpi-comparison.svg"
svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines()) + "\n", encoding="utf-8")
plt.close(fig)
