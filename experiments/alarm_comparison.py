"""
Compare Alarm Clock vs vanilla conditional XMult jokers.

Alarm Clock: X2 on last hand of round (fires once per blind).
Comparable vanilla jokers:
- The Duo: X2 if hand contains a Pair
- The Trio: X2 if hand contains a Three of a Kind
- The Family: X2 if hand contains a Four of a Kind
- The Order: X2 if hand contains a Straight
- The Tribe: X2 if hand contains a Flush
- Obelisk: XMult grows each hand you DON'T play most played type (resets on play)

Models: 8 antes, 3 blinds/ante, ~3.5 hands/blind.
"""

import matplotlib.pyplot as plt
import numpy as np

ANTES = 8
BLINDS_PER_ANTE = 3
HANDS_PER_BLIND = 3.5
N_SIMS = 1000

rng = np.random.default_rng(42)

# Build hand schedule
blind_hands = []
for ante in range(ANTES):
    for blind in range(BLINDS_PER_ANTE):
        n = int(HANDS_PER_BLIND) if blind < 2 else int(HANDS_PER_BLIND + 0.5)
        blind_hands.append(n)

total_hands = sum(blind_hands)

# Trigger probabilities for vanilla X2 jokers (per hand)
VANILLA_XMULT = {
    "The Duo (Pair)":       0.70,  # pairs are very common
    "The Tribe (Flush)":    0.15,  # flushes are uncommon
    "The Order (Straight)": 0.15,  # straights are uncommon
    "The Trio (3oaK)":      0.35,  # three of a kind moderate
    "The Family (4oaK)":    0.10,  # four of a kind rare
}

# --- Simulate ---
# For each joker: track XMult per hand (2.0 when fires, 1.0 when doesn't)
results = {}

# Alarm Clock: fires on last hand of each blind (deterministic)
alarm = np.ones((1, total_hands))
h = 0
for num_hands in blind_hands:
    for i in range(num_hands):
        if i == num_hands - 1:  # last hand of blind
            alarm[0, h] = 2.0
        h += 1
results["Alarm Clock"] = alarm

# Vanilla X2 jokers
for label, prob in VANILLA_XMULT.items():
    data = np.ones((N_SIMS, total_hands))
    for sim in range(N_SIMS):
        for h in range(total_hands):
            if rng.random() < prob:
                data[sim, h] = 2.0
    results[label] = data

# --- Compute stats ---
hands = np.arange(1, total_hands + 1)

ante_end_hands = []
cumul = 0
for ante in range(ANTES):
    for blind in range(BLINDS_PER_ANTE):
        n = int(HANDS_PER_BLIND) if blind < 2 else int(HANDS_PER_BLIND + 0.5)
        cumul += n
    ante_end_hands.append(cumul)

# --- Print summary ---
print("=" * 75)
print(f"Alarm Clock vs Vanilla X2 Mult Jokers ({N_SIMS} sims, {total_hands} hands)")
print("=" * 75)
print()
print(f"{'Joker':<25} {'Trigger%':>10} {'Fires/run':>10} {'Avg XMult':>10} {'Rarity':<12}")
print("-" * 75)

for label, data in results.items():
    fires = (data > 1.0).sum(axis=-1).mean()
    fire_pct = fires / total_hands * 100
    avg_xmult = data.mean(axis=-1).mean()  # geometric would be better but this shows the picture
    rarity = "Uncommon" if label == "Alarm Clock" else "Uncommon"
    print(f"{label:<25} {fire_pct:>9.1f}% {fires:>10.1f} {avg_xmult:>10.3f} {rarity:<12}")

# --- Effective score multiplier ---
# The real question: what's the cumulative scoring impact?
# X2 on 30% of hands vs X2 on 100% of last-hands
# Geometric mean of XMult across all hands
print()
print("Effective run multiplier (geometric mean of per-hand XMult):")
print("-" * 75)
for label, data in results.items():
    # Geometric mean = exp(mean(log(xmult)))
    log_mean = np.log(data).sum(axis=1).mean()
    geo_total = np.exp(log_mean)
    # Per-hand geometric mean
    geo_per_hand = geo_total ** (1.0 / total_hands)
    print(f"  {label:<25} total: X{geo_total:>8.1f}   per-hand: X{geo_per_hand:.4f}")

# --- Plot ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Left: trigger frequency comparison (bar chart)
labels = list(results.keys())
fire_rates = []
for label in labels:
    data = results[label]
    fire_rates.append((data > 1.0).sum(axis=-1).mean() / total_hands * 100)

colors = ["tab:red" if l == "Alarm Clock" else "tab:blue" for l in labels]
bars = ax1.barh(labels, fire_rates, color=colors, alpha=0.7)
ax1.set_xlabel("% of Hands Where X2 Fires")
ax1.set_title("Trigger Frequency: Alarm Clock vs Vanilla X2 Jokers")
ax1.grid(True, alpha=0.3, axis="x")

for bar, rate in zip(bars, fire_rates):
    ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
             f"{rate:.1f}%", va="center", fontsize=10)

# Right: cumulative XMult impact per blind
# Show how much total score boost each joker gives per blind
ax2_labels = []
ax2_values = []
ax2_errors = []
ax2_colors = []

for label in labels:
    data = results[label]
    # Per-blind: product of XMult values within each blind
    blind_boosts = []
    for sim in range(min(N_SIMS, data.shape[0])):
        h = 0
        for num_hands in blind_hands:
            blind_xmult = np.prod(data[sim, h:h+num_hands])
            blind_boosts.append(blind_xmult)
            h += num_hands

    ax2_labels.append(label)
    ax2_values.append(np.mean(blind_boosts))
    ax2_errors.append(np.std(blind_boosts))
    ax2_colors.append("tab:red" if label == "Alarm Clock" else "tab:blue")

bars2 = ax2.barh(ax2_labels, ax2_values, xerr=ax2_errors, color=ax2_colors, alpha=0.7, capsize=3)
ax2.set_xlabel("Avg Score Multiplier Per Blind (product of XMults)")
ax2.set_title("Effective Scoring Impact Per Blind (±1σ)")
ax2.grid(True, alpha=0.3, axis="x")

for bar, val in zip(bars2, ax2_values):
    ax2.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
             f"X{val:.2f}", va="center", fontsize=10)

plt.tight_layout()
plt.savefig("experiments/alarm_comparison.png", dpi=150)
plt.close()
print("\nSaved to experiments/alarm_comparison.png")
