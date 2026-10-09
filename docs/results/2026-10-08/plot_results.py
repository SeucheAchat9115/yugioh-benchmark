"""Render four performance/workflow-span plots from committed summaries."""
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "yugioh-sol-luna-runtime-20261008"
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter

root = Path(__file__).resolve().parent
read = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
runtime = read("runtime-summary.json")
provenance = read("provenance.json")
models = [
    ("sol", "gpt-6.1-sol", "GPT-6.1 Sol", "#2563eb", "o"),
    ("luna", "gpt-6-luna", "GPT-6 Luna", "#d97706", "D"),
]
data = []
for short, requested, label, color, marker in models:
    report = read(short + ".score.json")
    assert report["model"] == requested
    batches = [b for b in runtime["batches"] if b["model_requested"] == requested]
    for batch in batches:
        span = (datetime.fromisoformat(batch["last_recorded_action"])
                - datetime.fromisoformat(batch["first_recorded_action"])).total_seconds()
        assert abs(span - batch["completion_span_seconds"]) < 1e-6
        assert batch["source_run_file_sha256"] == provenance["models"][short]["run_file_sha256"]
    seconds = sum(b["completion_span_seconds"] for b in batches)
    assert sum(b["attempt_count"] for b in batches) == 36
    assert abs(seconds - runtime["totals"][requested]["recorded_span_seconds"]) < 1e-6
    data.append((label, color, marker, seconds / 60, report))

metrics = [
    ("state_recreation", "A · State recreation"),
    ("human_move_agreement", "B · Human-move agreement"),
    ("rule_correctness", "C · Rules correctness"),
    ("final_score", "Final · Equal-weight score"),
]

def panel(ax, key, title):
    for label, color, marker, minutes, report in data:
        score = (report["final_score_percent"] if key == "final_score"
                 else 100 * report["kpis"][key]["score"])
        ax.scatter(minutes, score, s=110, color=color, marker=marker,
                   edgecolor="white", linewidth=1.3, zorder=3)
        offset = (-12, -30) if score >= 90 else (12, 10)
        ax.annotate(f"{label}\n{score:.2f}%", (minutes, score),
                    xytext=offset, textcoords="offset points",
                    ha="right" if offset[0] < 0 else "left",
                    fontsize=10, color=color, fontweight="medium")
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlim(0, 52)
    ax.set_ylim(0, 105)
    ax.set_xticks(range(0, 51, 10))
    ax.set_yticks(range(0, 101, 20))
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.grid(color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0, pad=7, colors="#4b5563")

def save(fig, stem):
    fig.savefig(root / (stem + ".png"), dpi=180, facecolor="white")
    svg = root / (stem + ".svg")
    fig.savefig(svg, facecolor="white", metadata={"Date": None})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines())
                   + "\n", encoding="utf-8")
    plt.close(fig)

fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.6))
for ax, (key, title) in zip(axes.flat, metrics):
    panel(ax, key, title)
fig.suptitle("Performance vs recorded workflow span", x=0.06, ha="left",
             fontsize=20, fontweight="bold", color="#111827")
fig.text(0.06, 0.93, "18 reviewed positions · 36 tasks per model · independent checkpoint resets",
         fontsize=11, color="#4b5563")
legend = [Line2D([], [], color=c, marker=m, linestyle="None", markersize=9, label=label)
          for label, c, m, _, _ in data]
fig.legend(handles=legend, loc="upper right", bbox_to_anchor=(0.96, 0.987),
           ncol=2, frameon=False, fontsize=10)
fig.supxlabel("Recorded workflow span across all 36 tasks (minutes)", y=0.12, fontsize=11)
fig.supylabel("Performance", x=0.015, fontsize=11)
fig.text(0.06, 0.065, "Sol: 41m 36s (sum of two batch spans). Luna: 18m 37s. Host review and tool work included.",
         fontsize=9, color="#4b5563")
fig.text(0.06, 0.035, "Setup and first-response latency excluded. Prompts differed. This does not measure model inference speed.",
         fontsize=9, color="#4b5563")
fig.subplots_adjust(left=0.08, right=0.95, top=0.85, bottom=0.20, hspace=0.30, wspace=0.20)
save(fig, "performance-runtime")

for key, title in metrics:
    fig, ax = plt.subplots(figsize=(7, 5.2))
    panel(ax, key, title)
    ax.set_xlabel("Recorded workflow span across all 36 tasks (minutes)", labelpad=12)
    ax.set_ylabel("Performance")
    fig.text(0.08, 0.05, "Host work included; setup/first latency excluded. Not model inference time.",
             fontsize=9, color="#4b5563")
    fig.subplots_adjust(left=0.12, right=0.95, top=0.87, bottom=0.23)
    save(fig, "performance-runtime-" + key.replace("_", "-"))
