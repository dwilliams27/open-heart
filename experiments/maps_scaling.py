"""
Compare Maps joker scaling vs vanilla Balatro conditional mult jokers.

Maps: +20 Mult on Straight/SF, +5 permanent per trigger, +$2 per trigger.
Comparable vanilla jokers:
- Supernova: +Mult equal to times hand type has been played this run
- Sly Joker: +50 Chips if hand is a Pair (always-on conditional)
- Wily Joker: +100 Chips if hand is a Three of a Kind
- The Duo: X2 Mult if hand contains a Pair
- The Tribe: X2 Mult if hand contains a Flush
- Spare Trousers: +2 Mult per discard with Two Pair (scaling)

Models: 8 antes, ~3.5 hands/blind, variable straight frequency.
"""

import matplotlib.pyplot as plt
import numpy as np

# --- Run parameters ---
ANTES = 8
BLINDS_PER_ANTE = 3
HANDS_PER_BLIND = 3.5
N_SIMS = 1000

rng = np.random.default_rng(42)

# --- Build hand schedule ---
blind_hands = []
for ante in range(ANTES):
    for blind in range(BLINDS_PER_ANTE):
        n = int(HANDS_PER_BLIND) if blind < 2 else int(HANDS_PER_BLIND + 0.5)
        blind_hands.append(n)

total_hands = sum(blind_hands)

# --- Straight frequency scenarios ---
# Dedicated straight build: ~40% of hands are straights
# Occasional straights: ~15%
# Maps is conditional — frequency matters a lot
STRAIGHT_PROBS = {
    "Dedicated (40%)": 0.40,
    "Moderate (25%)": 0.25,
    "Occasional (15%)": 0.15,
}

# --- Simulate Maps across scenarios ---
maps_results = {}
maps_money = {}

for label, prob in STRAIGHT_PROBS.items():
    all_mult = np.zeros((N_SIMS, total_hands))
    all_money = np.zeros(N_SIMS)

    for sim in range(N_SIMS):
        bonus = 0
        money = 0
        h = 0
        for num_hands in blind_hands:
            for _ in range(num_hands):
                if rng.random() < prob:
                    mult = 20 + bonus
                    bonus += 5
                    money += 2
                    all_mult[sim, h] = mult
                else:
                    all_mult[sim, h] = 0
                h += 1
        all_money[sim] = money

    maps_results[label] = all_mult
    maps_money[label] = all_money

# --- Simulate vanilla comparisons (1000 sims) ---
# Supernova: +Mult equal to times this hand type played this run
# Assume player focuses one hand type, plays it ~60% of the time
supernova_all = np.zeros((N_SIMS, total_hands))
for sim in range(N_SIMS):
    play_count = 0
    h = 0
    for num_hands in blind_hands:
        for _ in range(num_hands):
            if rng.random() < 0.60:  # focused player
                play_count += 1
                supernova_all[sim, h] = play_count
            else:
                supernova_all[sim, h] = 0
            h += 1

# The Duo: X2 Mult if hand contains a Pair (~70% of hands contain a pair)
# Convert to effective mult boost for comparison: assume base mult ~10 early, ~30 late
# X2 means +base_mult, so effective flat mult added = base_mult
# For simplicity, model as flat equivalent
duo_all = np.zeros((N_SIMS, total_hands))
pair_prob = 0.70
for sim in range(N_SIMS):
    h = 0
    for ante_idx in range(ANTES):
        base_mult = 8 + ante_idx * 4  # rough base mult scaling
        for blind in range(BLINDS_PER_ANTE):
            n = int(HANDS_PER_BLIND) if blind < 2 else int(HANDS_PER_BLIND + 0.5)
            for _ in range(n):
                if rng.random() < pair_prob:
                    duo_all[sim, h] = base_mult  # X2 = adding base_mult
                h += 1

# --- Ante boundaries ---
ante_end_hands = []
cumul = 0
for ante in range(ANTES):
    for blind in range(BLINDS_PER_ANTE):
        n = int(HANDS_PER_BLIND) if blind < 2 else int(HANDS_PER_BLIND + 0.5)
        cumul += n
    ante_end_hands.append(cumul)

a1, a4, a8 = ante_end_hands[0] - 1, ante_end_hands[3] - 1, ante_end_hands[7] - 1

# --- Compute cumulative average mult per hand (running average of non-zero) ---
def running_avg_nonzero(arr):
    """For each hand, compute average mult contribution so far (total mult / total hands)."""
    cumsum = np.cumsum(arr, axis=1)
    counts = np.arange(1, arr.shape[1] + 1)
    return cumsum / counts

# --- Print summary ---
print("=" * 75)
print(f"Maps Scaling Experiment: {ANTES} antes, {total_hands} hands, {N_SIMS} sims")
print("=" * 75)
print()

print("Maps: Mult per trigger (when it fires) at key points")
print("-" * 75)
print(f"{'Scenario':<22} {'Triggers':>10} {'Avg Mult/trig A4':>18} {'Avg Mult/trig A8':>18} {'Total $':>10}")
print("-" * 75)

for label, prob in STRAIGHT_PROBS.items():
    all_mult = maps_results[label]
    money = maps_money[label]

    # Average mult when it fires (non-zero entries)
    mask_a4 = all_mult[:, :ante_end_hands[3]] > 0
    mask_a8 = all_mult > 0

    triggers = mask_a8.sum(axis=1).mean()
    avg_mult_a4 = np.array([all_mult[s, :ante_end_hands[3]][mask_a4[s]].mean()
                            if mask_a4[s].any() else 0 for s in range(N_SIMS)]).mean()
    avg_mult_a8 = np.array([all_mult[s][mask_a8[s]].mean()
                            if mask_a8[s].any() else 0 for s in range(N_SIMS)]).mean()
    avg_money = money.mean()

    print(f"{label:<22} {triggers:>10.1f} {avg_mult_a4:>18.1f} {avg_mult_a8:>18.1f} {avg_money:>9.0f}")

print()
print("Comparison: Average mult added per hand (across ALL hands, including misses)")
print("-" * 75)
print(f"{'Joker':<22} {'Type':<10} {'Avg/hand A1':>12} {'Avg/hand A4':>12} {'Avg/hand A8':>12}")
print("-" * 75)

for label in STRAIGHT_PROBS:
    all_mult = maps_results[label]
    avg = all_mult.mean(axis=0)
    print(f"Maps {label.split('(')[1].rstrip(')'):<16} {'Mult':<10} {avg[:ante_end_hands[0]].mean():>12.1f} {avg[:ante_end_hands[3]].mean():>12.1f} {avg.mean():>12.1f}")

supernova_avg = supernova_all.mean(axis=0)
print(f"{'Supernova (60%)':<22} {'Mult':<10} {supernova_avg[:ante_end_hands[0]].mean():>12.1f} {supernova_avg[:ante_end_hands[3]].mean():>12.1f} {supernova_avg.mean():>12.1f}")

duo_avg = duo_all.mean(axis=0)
print(f"{'The Duo (70% pair)':<22} {'~Mult':<10} {duo_avg[:ante_end_hands[0]].mean():>12.1f} {duo_avg[:ante_end_hands[3]].mean():>12.1f} {duo_avg.mean():>12.1f}")

# --- Plot ---
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
hands = np.arange(1, total_hands + 1)

# Left: Maps mult per trigger over time (by scenario)
ax1 = axes[0]
colors = {"Dedicated (40%)": "tab:red", "Moderate (25%)": "tab:orange", "Occasional (15%)": "tab:blue"}
for label in STRAIGHT_PROBS:
    all_mult = maps_results[label]
    # For each hand position, average the mult value WHEN it fires
    avg_when_fires = np.zeros(total_hands)
    for h in range(total_hands):
        vals = all_mult[:, h]
        fires = vals[vals > 0]
        avg_when_fires[h] = fires.mean() if len(fires) > 0 else np.nan
    ax1.plot(hands, avg_when_fires, label=f"Maps {label}", linewidth=2, color=colors[label])

for i, ae in enumerate(ante_end_hands):
    ax1.axvline(x=ae, color="gray", alpha=0.3)
    ax1.text(ae, ax1.get_ylim()[0] if ax1.get_ylim()[0] > 0 else 20, f" A{i+1}", fontsize=8, color="gray")

ax1.set_xlabel("Hands Played")
ax1.set_ylabel("Mult (when triggered)")
ax1.set_title("Maps: Mult Per Trigger Over Time")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# Middle: Average mult per hand comparison (all jokers)
ax2 = axes[1]
for label in STRAIGHT_PROBS:
    all_mult = maps_results[label]
    avg = all_mult.mean(axis=0)
    std = all_mult.std(axis=0)
    ax2.plot(hands, avg, label=f"Maps {label}", linewidth=2, color=colors[label])
    ax2.fill_between(hands, avg - std, avg + std, color=colors[label], alpha=0.1)

supernova_mean = supernova_all.mean(axis=0)
supernova_std = supernova_all.std(axis=0)
ax2.plot(hands, supernova_mean, label="Supernova (60%)", linewidth=2, color="tab:green", linestyle="--")
ax2.fill_between(hands, supernova_mean - supernova_std, supernova_mean + supernova_std, color="tab:green", alpha=0.1)

duo_mean = duo_all.mean(axis=0)
duo_std = duo_all.std(axis=0)
ax2.plot(hands, duo_mean, label="The Duo (X2, 70%)", linewidth=2, color="tab:purple", linestyle=":")
ax2.fill_between(hands, duo_mean - duo_std, duo_mean + duo_std, color="tab:purple", alpha=0.1)

for i, ae in enumerate(ante_end_hands):
    ax2.axvline(x=ae, color="gray", alpha=0.3)

ax2.set_xlabel("Hands Played")
ax2.set_ylabel("Avg Mult Added Per Hand")
ax2.set_title(f"Mult/Hand Comparison ({N_SIMS} sims, ±1σ)")
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

# Right: Money earned by Maps
ax3 = axes[2]
money_data = [maps_money[label] for label in STRAIGHT_PROBS]
money_labels = [label.split("(")[1].rstrip(")") for label in STRAIGHT_PROBS]
bp = ax3.boxplot(money_data, labels=money_labels, patch_artist=True)
color_list = [colors[label] for label in STRAIGHT_PROBS]
for patch, c in zip(bp['boxes'], color_list):
    patch.set_facecolor(c)
    patch.set_alpha(0.5)

ax3.set_ylabel("Total $ Earned")
ax3.set_title("Maps: Money Generated Over Full Run")
ax3.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("experiments/maps_scaling.png", dpi=150)
plt.close()
print("\nSaved to experiments/maps_scaling.png")
