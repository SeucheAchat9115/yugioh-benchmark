"""Render current checkpoint results from public aggregate summaries only."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "yugioh-native-luna-20261009"
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parent
METRICS = (
    ("state_recreation", "State recreation"),
    ("human_move_agreement", "Human-move agreement"),
    ("rule_correctness", "Rule correctness"),
    ("final_score", "Equal-weight final score"),
)
COLOR = "#d97706"


def save(fig, stem):
    for extension in ("png", "svg"):
        path = ROOT / f"{stem}.{extension}"
        fig.savefig(path, dpi=180,
                    facecolor="white", metadata={"Date": None} if extension == "svg" else None)
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def style(ax, title):
    ax.set_title(title, loc="left", pad=14, fontweight="bold")
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20))
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.set_ylabel("Performance")
    ax.grid(axis="y", color="#e5e7eb")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)


def value(score, key):
    return (score["final_score_percent"] if key == "final_score"
            else 100 * score["kpis"][key]["score"])


def main():
    score = json.loads((ROOT / "luna.score.json").read_text())
    measurements = json.loads((ROOT / "measurements.json").read_text())
    assert score["model"] == measurements["model"] == "gpt-6-luna"
    assert len(score["outcomes"]) == 36
    assert all(not outcome["pending"] for outcome in score["outcomes"])
    assert abs(score["final_score_percent"] - sum(
        100 * score["kpis"][key]["score"] * weight
        for key, weight in score["weights"].items())) < 1e-9

    fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
    style(ax, "GPT-6 Luna · 36 reviewed checkpoint tasks")
    for index, (key, _) in enumerate(METRICS):
        y = value(score, key)
        ax.bar(index, y, color=COLOR if key != "final_score" else "#22775d", width=.6)
        count = "" if key == "final_score" else (
            f"\n{score['kpis'][key]['passed']}/{score['kpis'][key]['total']}")
        ax.text(index, y + 2, f"{y:.2f}%{count}", ha="center")
    ax.set_xticks(range(4), [title.replace(" ", "\n", 1) for _, title in METRICS])
    save(fig, "performance")

    for axis, field, unit in (
        ("runtime", "evaluation_minutes", "Evaluated-model runtime (minutes)"),
        ("cost", "evaluation_cost_usd", "Evaluated-model cost (USD)"),
    ):
        x = measurements[field]

        def panel(ax, key, title):
            style(ax, title)
            y = value(score, key)
            if x is None:
                # A categorical location, explicitly unrelated to a numeric zero.
                ax.set_xlim(-.7, .7)
                ax.set_xticks([0], ["Unavailable"])
                ax.set_xlabel(unit + " · unmeasured")
                position = 0
            else:
                assert x >= 0
                position = float(x)
                ax.set_xlim(0, max(1, position * 1.6))
                ax.set_xlabel(unit)
            ax.scatter(position, y, s=110, color=COLOR, marker="D", zorder=3)
            ax.annotate(f"GPT-6 Luna · {y:.2f}%", (position, y),
                        xytext=(0, 10), textcoords="offset points", ha="center", fontsize=10)

        fig, panels = plt.subplots(2, 2, figsize=(11, 8.5), layout="constrained")
        for ax, (key, title) in zip(panels.flat, METRICS):
            panel(ax, key, title)
        fig.suptitle(f"Performance vs {axis} · GPT-6 Luna\n"
                     "18 reviewed positions · 36 tasks · cooperative native subagents", fontsize=15)
        footer = ("USD cost unavailable: token usage and billing were not reported. No zero-cost estimate."
                  if axis == "cost" else
                  "Comparable runtime unavailable: archival reuse and coordinator preparation prevent inference timing.")
        fig.supxlabel(footer, fontsize=10)
        save(fig, f"performance-{axis}")

        for key, title in METRICS:
            fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
            panel(ax, key, title)
            fig.supxlabel(footer.replace(": ", ":\n", 1), fontsize=9)
            save(fig, f"performance-{axis}-{key.replace('_', '-')}")


if __name__ == "__main__":
    main()
