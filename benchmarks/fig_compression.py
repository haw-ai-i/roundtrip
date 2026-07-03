"""Stage 1 figure: roundtrip fidelity vs compression (words/line)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

data = [
    ("contains",      7.58, 1.00),
    ("unitsystem",    6.66, 0.85),
    ("saferepr",     12.36, 0.73),
    ("tensorproduct", 3.76, 0.62),
    ("prefixes",      4.89, 0.00),
    ("ndim_array",    3.63, 0.00),
]
labels=[d[0] for d in data]; x=[d[1] for d in data]; y=[d[2] for d in data]
fig, ax = plt.subplots(figsize=(6.5,4.5))
ax.scatter(x,y,s=90,color="#1D9E75",edgecolor="#0F6E56",zorder=3)
for lab,xi,yi in zip(labels,x,y):
    ax.annotate(lab,(xi,yi),textcoords="offset points",xytext=(7,5),fontsize=9)
ax.set_xlabel("description density (words per code line)")
ax.set_ylabel("roundtrip pass fraction")
ax.set_title("Stage 1: regeneration fidelity vs description density")
ax.grid(True,alpha=0.25,zorder=0); ax.set_ylim(-0.05,1.08)
fig.tight_layout(); fig.savefig("benchmarks/fig_compression.png",dpi=160); fig.savefig("benchmarks/fig_compression.svg")
print("saved benchmarks/fig_compression.png + .svg")
