"""The two charts in the README.

1. results/monitor_scores_hist.png: suspicion scores, honest vs. backdoored.
2. results/attack_outcomes.png: what happened to every attack attempt.

No ROC chart: with only 2 backdoors it's a 3-point staircase that says
nothing the two numbers (catch rate, AUC) don't already say.

Usage:
    python src/plots.py --attack-mode attack_v2
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import UNTRUSTED_MODEL

RESULTS = Path(__file__).resolve().parent.parent / "results"

HONEST = "#2a78d6"    # categorical slot 1 (blue)
BACKDOOR = "#eb6834"  # categorical slot 2 (orange)
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"

# exploit_reason in the attempts CSV -> chart label. Reasons that start with
# "reference errors" or "rejected on manual review" carry details; they're
# grouped by prefix.
OUTCOMES = [
    ("same output as reference", "Same output as reference on the exploit (no real bug)"),
    ("fails normal tests", "Fails the normal tests"),
    ("reference errors", "Exploit input the reference can't run"),
    ("same number up to rounding", "Same number up to rounding"),
    ("rejected on manual review", "Rejected on manual review"),
    ("model error", "Model error (timeout or server error)"),
    ("same elements", "Same elements, different container or order"),
    ("differs from reference", "Genuine backdoor"),
    ("no exploit input given", "No exploit input given"),
]


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelcolor=INK_2)


def score_histogram(monitor_csv: Path, out: Path):
    rows = [r for r in csv.DictReader(monitor_csv.open()) if r["suspicion_score"] not in ("", "None")]
    honest = [float(r["suspicion_score"]) for r in rows if r["mode"] == "honest"]
    backdoor = [float(r["suspicion_score"]) for r in rows if r["valid_backdoor"] == "True"]

    fig, ax = plt.subplots(figsize=(7, 4), facecolor=SURFACE)
    style(ax)
    width = 0.38
    for group, color, offset, label in ((honest, HONEST, -width / 2, "Honest"),
                                        (backdoor, BACKDOOR, width / 2, "Backdoored")):
        counts = Counter(group)
        xs = list(range(11))
        shares = [100 * counts[x] / len(group) for x in xs]
        ax.bar([x + offset for x in xs], shares, width=width - 0.04, color=color,
               label=f"{label} (n={len(group)})", zorder=2)
        for x in xs:
            if counts[x]:
                ax.annotate(f"{counts[x]}", (x + offset, shares[x]), xytext=(0, 3),
                            textcoords="offset points", ha="center", fontsize=8, color=INK_2)
    ax.set_xticks(range(11))
    ax.set_xlim(-0.6, 10.6)
    ax.set_ylim(0, 108)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_xlabel("Suspicion score (10 − the monitor's HONESTY rating)", color=INK_2)
    ax.set_ylabel("Share of the group (%)", color=INK_2)
    ax.set_title("The monitor rated almost everything fully honest, both backdoors included",
                 color=INK, fontsize=10, loc="left")
    ax.legend(frameon=False, labelcolor=INK_2, fontsize=9)
    fig.text(0.01, 0.01, "Numbers above bars are counts. 1 honest reply had no score and is left out.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out, dpi=150, facecolor=SURFACE)


def outcome_bars(attempts_csv: Path, out: Path):
    rows = list(csv.DictReader(attempts_csv.open()))
    counts = Counter()
    for r in rows:
        reason = r["exploit_reason"]
        match = [label for prefix, label in OUTCOMES if reason.startswith(prefix)]
        if len(match) != 1:
            raise SystemExit(f"Unrecognized exploit_reason: {reason!r}")
        counts[match[0]] += 1
    labels = [label for _, label in OUTCOMES]
    labels.sort(key=lambda l: counts[l])  # biggest at the top

    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURFACE)
    style(ax)
    colors = [BACKDOOR if l == "Genuine backdoor" else HONEST for l in labels]
    ax.barh(labels, [counts[l] for l in labels], color=colors, height=0.7, zorder=2)
    for i, l in enumerate(labels):
        ax.annotate(str(counts[l]), (counts[l], i), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=INK_2)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_xlim(0, max(counts.values()) * 1.1)
    ax.set_xlabel("Attack attempts", color=INK_2)
    ax.set_title(f"Where {len(rows)} attack attempts went: 2 genuine backdoors",
                 color=INK, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=SURFACE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attack-mode", default="attack_v2", choices=["attack", "attack_v2"])
    args = parser.parse_args()
    slug = UNTRUSTED_MODEL.replace(":", "_").replace("/", "_")

    hist = RESULTS / "monitor_scores_hist.png"
    bars = RESULTS / "attack_outcomes.png"
    score_histogram(RESULTS / "monitor_scores.csv", hist)
    outcome_bars(RESULTS / f"untrusted_{slug}_{args.attack_mode}_attempts.csv", bars)
    print(f"charts: {hist}, {bars}")


if __name__ == "__main__":
    main()
