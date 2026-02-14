"""
Compare Fitness Tracker chip scaling vs vanilla Balatro scaling jokers.

Models a typical run: 8 antes, ~3.5 hands per blind, 3 blinds per ante.
Stochastic jokers (Runner, Square) averaged over 1000 simulations with std dev.
"""

import matplotlib.pyplot as plt
import numpy as np

# --- Run parameters ---
ANTES = 8
BLINDS_PER_ANTE = 3  # small, big, boss
HANDS_PER_BLIND = 3.5  # average hands used to beat a blind
CARDS_PER_HAND = 4.5  # average cards played per hand (mix of pairs, 3oaK, straights)
DISCARDS_PER_BLIND = 2.0  # average discards used per blind
N_SIMS = 1000  # simulations for stochastic jokers

straight_prob = 0.15  # ~15% of hands are straights
four_card_prob = 0.35  # ~35% of hands are exactly 4 cards

# --- Build hand schedule (deterministic) ---
blind_hands = []
for ante in range(ANTES):
    for blind in range(BLINDS_PER_ANTE):
        n = int(HANDS_PER_BLIND) if blind < 2 else int(HANDS_PER_BLIND + 0.5)
        blind_hands.append((ante, blind, n))

total_hands = sum(n for _, _, n in blind_hands)

# --- Deterministic jokers (single pass) ---
fitness_chips = np.zeros(total_hands)
green_mult = np.zeros(total_hands)
ice_cream_chips = np.zeros(total_hands)

fitness_total = 0
green_total = 0
ice_total = 100.0
h = 0
for ante, blind, num_hands in blind_hands:
    for _ in range(num_hands):
        fitness_total = min(150, fitness_total + CARDS_PER_HAND)
        green_total += 1
        ice_total = max(0, ice_total - 5)
        fitness_chips[h] = fitness_total
        green_mult[h] = green_total
        ice_cream_chips[h] = ice_total
        h += 1
    for _ in range(int(DISCARDS_PER_BLIND)):
        green_total = max(0, green_total - 1)

# --- Stochastic jokers (N_SIMS passes) ---
rng = np.random.default_rng(42)
runner_all = np.zeros((N_SIMS, total_hands))
square_all = np.zeros((N_SIMS, total_hands))

for sim in range(N_SIMS):
    runner_total = 0
    square_total = 0
    h = 0
    for ante, blind, num_hands in blind_hands:
        for _ in range(num_hands):
            if rng.random() < straight_prob:
                runner_total += 15
            if rng.random() < four_card_prob:
                square_total += 4
            runner_all[sim, h] = runner_total
            square_all[sim, h] = square_total
            h += 1

runner_mean = runner_all.mean(axis=0)
runner_std = runner_all.std(axis=0)
square_mean = square_all.mean(axis=0)
square_std = square_all.std(axis=0)

hands = np.arange(1, total_hands + 1)

# --- Ante boundaries ---
ante_end_hands = []
h = 0
for ante in range(ANTES):
    for _, _, n in blind_hands:
        pass
ante_cumul = 0
ante_end_hands = []
for ante in range(ANTES):
    for blind in range(BLINDS_PER_ANTE):
        n = int(HANDS_PER_BLIND) if blind < 2 else int(HANDS_PER_BLIND + 0.5)
        ante_cumul += n
    ante_end_hands.append(ante_cumul)

a1, a4, a8 = ante_end_hands[0] - 1, ante_end_hands[3] - 1, ante_end_hands[7] - 1

# --- Print summary table ---
print("=" * 70)
print(f"Run simulation: {ANTES} antes, ~{HANDS_PER_BLIND} hands/blind, {CARDS_PER_HAND} cards/hand")
print(f"Total hands played: {total_hands} | Stochastic jokers: {N_SIMS} sims")
print("=" * 70)
print()
print(f"{'Joker':<20} {'Type':<8} {'Ante 1':>10} {'Ante 4':>10} {'Ante 8':>10}")
print("-" * 70)
print(f"{'Fitness Tracker':<20} {'Chips':<8} {fitness_chips[a1]:>10.0f} {fitness_chips[a4]:>10.0f} {fitness_chips[a8]:>10.0f}")
print(f"{'Green Joker':<20} {'Mult':<8} {green_mult[a1]:>10.0f} {green_mult[a4]:>10.0f} {green_mult[a8]:>10.0f}")
print(f"{'Ice Cream':<20} {'Chips':<8} {ice_cream_chips[a1]:>10.0f} {ice_cream_chips[a4]:>10.0f} {ice_cream_chips[a8]:>10.0f}")
print(f"{'Runner':<20} {'Chips':<8} {runner_mean[a1]:>7.0f}±{runner_std[a1]:<2.0f} {runner_mean[a4]:>7.0f}±{runner_std[a4]:<2.0f} {runner_mean[a8]:>7.0f}±{runner_std[a8]:<2.0f}")
print(f"{'Square Joker':<20} {'Chips':<8} {square_mean[a1]:>7.0f}±{square_std[a1]:<2.0f} {square_mean[a4]:>7.0f}±{square_std[a4]:<2.0f} {square_mean[a8]:>7.0f}±{square_std[a8]:<2.0f}")

# --- Plot ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Left: scaling curves with error bands for stochastic jokers
ax1.plot(hands, fitness_chips, label="Fitness Tracker (Chips, cap 150)", linewidth=2.5, color="tab:red")
ax1.plot(hands, green_mult, label="Green Joker (Mult)", linewidth=2, color="tab:green", linestyle="--")
ax1.plot(hands, ice_cream_chips, label="Ice Cream (Chips)", linewidth=2, color="tab:cyan", linestyle="--")

ax1.plot(hands, runner_mean, label="Runner (Chips, 15% straight)", linewidth=2, color="tab:orange", linestyle=":")
ax1.fill_between(hands, runner_mean - runner_std, runner_mean + runner_std, color="tab:orange", alpha=0.15)

ax1.plot(hands, square_mean, label="Square Joker (Chips, 35% 4-card)", linewidth=2, color="tab:purple", linestyle=":")
ax1.fill_between(hands, square_mean - square_std, square_mean + square_std, color="tab:purple", alpha=0.15)

# Mark ante boundaries
for i, ae in enumerate(ante_end_hands):
    ax1.axvline(x=ae, color="gray", alpha=0.3, linestyle="-")
    ax1.text(ae, ax1.get_ylim()[0], f" A{i+1}", fontsize=8, color="gray", va="bottom")

ax1.set_xlabel("Hands Played")
ax1.set_ylabel("Bonus Value")
ax1.set_title(f"Scaling Comparison (stochastic: {N_SIMS} sims, ±1σ bands)")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# Right: Fitness Tracker breakdown by ante
ante_labels = [f"Ante {i+1}" for i in range(ANTES)]
ante_values = [fitness_chips[ae - 1] for ae in ante_end_hands]
ante_increments = [ante_values[0]] + [ante_values[i] - ante_values[i-1] for i in range(1, ANTES)]

bars = ax2.bar(ante_labels, ante_values, color="tab:red", alpha=0.7, label="Cumulative Chips")
ax2.bar(ante_labels, ante_increments, color="tab:red", alpha=0.3, label="Chips gained this ante")

for bar, val in zip(bars, ante_values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
             f"+{val:.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

ax2.set_ylabel("Chips")
ax2.set_title("Fitness Tracker Accumulation Per Ante")
ax2.legend()
ax2.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("experiments/fitness_scaling_capped.png", dpi=150)
plt.close()
print("\nSaved to experiments/fitness_scaling_capped.png")
