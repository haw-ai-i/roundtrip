import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

iters = [0, 1, 2, 3]
objective = [0.326, 0.540, 0.567, 0.646]
fidelity = [0.737, 1.000, 1.000, 1.000]
ax1.plot(iters, objective, "o-", color="#1D9E75", linewidth=2, markersize=8, label="objective", zorder=3)
ax1.plot(iters, fidelity, "s--", color="#534AB7", linewidth=1.5, markersize=6, label="fidelity", zorder=2)
ax1.set_xlabel("optimization iteration")
ax1.set_ylabel("score")
ax1.set_title("Optimizing the describe prompt")
ax1.set_xticks(iters); ax1.set_ylim(0, 1.08); ax1.grid(True, alpha=0.25)
ax1.legend(loc="lower right", fontsize=9)

labels = ["baseline", "discovered"]
heldout = [0.500, 1.000]
bars = ax2.bar(labels, heldout, color=["#B0AEA6", "#1D9E75"], width=0.55, zorder=3)
ax2.set_ylabel("held-out fidelity")
ax2.set_title("Generalization to unseen fixtures")
ax2.set_ylim(0, 1.15); ax2.grid(True, axis="y", alpha=0.25)
for b, v in zip(bars, heldout):
    ax2.text(b.get_x()+b.get_width()/2, v+0.03, f"{v:.2f}", ha="center", fontsize=10)

fig.tight_layout()
fig.savefig("benchmarks/fig_stage3.png", dpi=160)
fig.savefig("benchmarks/fig_stage3.svg")
print("saved benchmarks/fig_stage3.png + .svg")
