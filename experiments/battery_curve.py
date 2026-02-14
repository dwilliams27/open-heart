"""
Experiment 5: Battery Charge Curve

Models Battery's average Mult contribution as a function of play style.
Compares aggressive (use all hands) vs conservative (win fast) strategies.
Sweeps starting charge and decay rate parameters.

Usage:
    python experiments/battery_curve.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring_model import (
    HandType, HAND_NAMES, make_deck, best_play_fast, score_hand,
    BLIND_SCORES, Battery, hand_base_score,
)
import random
from collections import defaultdict


HANDS_PER_BLIND = 4
N_SIMULATIONS = 3000


def battery_xmult_per_hand(start_charge=3.0, decay=0.25, hands_used=4):
    """Compute the XMult Battery provides for each hand in a blind."""
    return [max(start_charge - decay * h, 0.0) for h in range(hands_used)]


def print_charge_table():
    """Show Battery's XMult value for each hand number with different parameters."""
    print("=" * 70)
    print("Battery Charge Table: XMult Per Hand")
    print("=" * 70)

    configs = [
        ("Conservative (X2.5, -0.2)", 2.5, 0.2),
        ("Design (X3.0, -0.25)", 3.0, 0.25),
        ("Aggressive (X3.5, -0.3)", 3.5, 0.3),
    ]

    print(f"\n  {'Config':<30}", end="")
    for h in range(1, 9):
        print(f"  Hand {h}", end="")
    print(f"  {'Avg(4h)':>8}")
    print(f"  {'-' * 100}")

    for name, start, decay in configs:
        print(f"  {name:<30}", end="")
        xmults = battery_xmult_per_hand(start, decay, 8)
        for xm in xmults:
            print(f"  {xm:>5.2f}x", end="")
        avg4 = sum(xmults[:4]) / 4
        print(f"  {avg4:>7.2f}x")


def simulate_recharge_rate():
    """
    Simulate how often a player beats a blind with hands remaining (triggering recharge).
    """
    print("\n" + "=" * 70)
    print("Recharge Probability: How Often Do Players Win Efficiently?")
    print("=" * 70)

    random.seed(42)
    deck = make_deck()

    # For each Ante, simulate blinds and see how many hands it takes to beat them
    EXPECTED_LEVELS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5}

    print(f"\n  {'Ante':>4}  {'Blind':>8}  {'Avg Hands':>10}  {'1-Hand%':>8}  "
          f"{'2-Hand%':>8}  {'3-Hand%':>8}  {'4-Hand%':>8}  {'Recharge%':>10}")
    print(f"  {'-' * 80}")

    for ante in range(1, 9):
        boss_req = BLIND_SCORES["Boss"][ante - 1]
        level = EXPECTED_LEVELS[ante]
        levels = {ht: level for ht in HandType}

        hand_counts = defaultdict(int)
        total_wins = 0

        for _ in range(N_SIMULATIONS):
            d = list(deck)
            random.shuffle(d)
            draw_pile = list(d)
            cumulative_score = 0
            hands_used = 0

            for h in range(HANDS_PER_BLIND):
                if len(draw_pile) < 8:
                    draw_pile = list(d)
                    random.shuffle(draw_pile)
                hand = draw_pile[:8]
                draw_pile = draw_pile[8:]

                _, played, scoring = best_play_fast(hand)
                score, _, _ = score_hand(played, hand_levels=levels)
                cumulative_score += score
                hands_used += 1

                if cumulative_score >= boss_req:
                    break

            if cumulative_score >= boss_req:
                hand_counts[hands_used] += 1
                total_wins += 1

        if total_wins == 0:
            print(f"  {ante:>4}  {boss_req:>8,}  {'N/A':>10}  (no wins without jokers)")
            continue

        avg_hands = sum(h * c for h, c in hand_counts.items()) / total_wins
        recharge_pct = sum(c for h, c in hand_counts.items() if h < HANDS_PER_BLIND) / N_SIMULATIONS * 100
        h1 = hand_counts.get(1, 0) / N_SIMULATIONS * 100
        h2 = hand_counts.get(2, 0) / N_SIMULATIONS * 100
        h3 = hand_counts.get(3, 0) / N_SIMULATIONS * 100
        h4 = hand_counts.get(4, 0) / N_SIMULATIONS * 100

        print(f"  {ante:>4}  {boss_req:>8,}  {avg_hands:>10.2f}  {h1:>7.1f}%  "
              f"{h2:>7.1f}%  {h3:>7.1f}%  {h4:>7.1f}%  {recharge_pct:>9.1f}%")


def ev_analysis():
    """
    Compute Battery's expected XMult contribution accounting for recharge probability.
    """
    print("\n" + "=" * 70)
    print("Battery EV Analysis: Expected XMult Per Hand")
    print("=" * 70)

    configs = [
        ("X2.5, -0.20", 2.5, 0.20),
        ("X3.0, -0.25", 3.0, 0.25),
        ("X3.5, -0.30", 3.5, 0.30),
    ]

    # For each config, show effective XMult for different playstyles
    playstyles = [
        ("Always 1 hand", 1),
        ("Usually 2 hands", 2),
        ("Usually 3 hands", 3),
        ("Always 4 hands", 4),
    ]

    print(f"\n  {'Config':<16} {'Playstyle':<20} {'Avg XMult':>10} "
          f"{'Score Mult':>11} {'Recharges?':>10}")
    print(f"  {'-' * 70}")

    for config_name, start, decay in configs:
        for style_name, hands_used in playstyles:
            xmults = battery_xmult_per_hand(start, decay, hands_used)
            avg_xmult = sum(xmults) / len(xmults) if xmults else 1.0
            # The geometric mean is more relevant for score impact
            product = 1.0
            for xm in xmults:
                product *= max(xm, 0.01)
            geo_mean = product ** (1 / len(xmults)) if xmults else 1.0
            recharges = "Yes" if hands_used < HANDS_PER_BLIND else "No"
            print(f"  {config_name:<16} {style_name:<20} {avg_xmult:>10.2f}x "
                  f"{geo_mean:>10.2f}x {recharges:>10}")
        print()


def score_impact_simulation():
    """
    Simulate actual score impact of Battery across Antes.
    """
    print("\n" + "=" * 70)
    print("Battery Score Impact: Simulated Across Antes")
    print("=" * 70)

    random.seed(42)
    deck = make_deck()
    EXPECTED_LEVELS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5}

    print(f"\n  {'Ante':>4}  {'No Battery':>11}  {'Hand 1':>11}  {'Hand 2':>11}  "
          f"{'Hand 3':>11}  {'Hand 4':>11}")
    print(f"  {'-' * 65}")

    for ante in range(1, 9):
        level = EXPECTED_LEVELS[ante]
        levels = {ht: level for ht in HandType}

        scores_base = []
        scores_by_hand = {h: [] for h in range(1, 5)}

        for _ in range(5000):
            d = list(deck)
            random.shuffle(d)
            hand = d[:8]
            _, played, scoring = best_play_fast(hand)

            score_b, _, _ = score_hand(played, hand_levels=levels)
            scores_base.append(score_b)

            for h in range(1, 5):
                battery = Battery()
                score_bat, _, _ = score_hand(
                    played, jokers=[battery], hand_levels=levels,
                    hand_number_in_blind=h,
                )
                scores_by_hand[h].append(score_bat)

        avg_base = sum(scores_base) / len(scores_base)
        avgs = {h: sum(s) / len(s) for h, s in scores_by_hand.items()}
        print(f"  {ante:>4}  {avg_base:>11,.0f}  ", end="")
        for h in range(1, 5):
            ratio = avgs[h] / avg_base if avg_base > 0 else 0
            print(f"{avgs[h]:>8,.0f}({ratio:.1f}x)", end=" ")
        print()


def parameter_sweep():
    """Sweep start charge and decay to find sweet spot."""
    print("\n" + "=" * 70)
    print("Parameter Sweep: Optimal Battery Values")
    print("=" * 70)
    print("  Target: avg XMult of 2.0-2.5 over a typical 3-hand blind")

    print(f"\n  {'Start':>5}  {'Decay':>5}  {'Avg 2h':>7}  {'Avg 3h':>7}  {'Avg 4h':>7}  "
          f"{'Dead@':>6}  {'Verdict':>10}")
    print(f"  {'-' * 60}")

    for start in [2.0, 2.5, 3.0, 3.5, 4.0]:
        for decay in [0.15, 0.20, 0.25, 0.30, 0.40]:
            xmults = battery_xmult_per_hand(start, decay, 12)
            avg2 = sum(xmults[:2]) / 2
            avg3 = sum(xmults[:3]) / 3
            avg4 = sum(xmults[:4]) / 4

            # When does it hit 0?
            dead_at = next((h + 1 for h, xm in enumerate(xmults) if xm <= 0), ">12")

            # Verdict: is avg 3-hand in [2.0, 2.5]?
            if 2.0 <= avg3 <= 2.5:
                verdict = "SWEET SPOT"
            elif avg3 < 2.0:
                verdict = "too weak"
            else:
                verdict = "too strong"

            dead_str = str(dead_at) if isinstance(dead_at, int) else dead_at
            print(f"  {start:>5.1f}  {decay:>5.2f}  {avg2:>7.2f}  {avg3:>7.2f}  "
                  f"{avg4:>7.2f}  {dead_str:>6}  {verdict:>10}")


def main():
    print_charge_table()
    simulate_recharge_rate()
    ev_analysis()
    score_impact_simulation()
    parameter_sweep()

    print(f"\n{'=' * 70}")
    print("KEY FINDINGS:")
    print(f"{'=' * 70}")
    print("""
  Questions answered:
  1. What's Battery's average XMult over a typical blind?
  2. How often do players recharge (beat blind with hands remaining)?
  3. Does Battery reward skill (efficient play) meaningfully?
  4. What start/decay values hit the X2.0-2.5 target?

  Battery should:
  - Feel incredible on hand 1 (X3 or higher)
  - Still be good on hand 3 (X2+)
  - Create genuine tension: "do I need another hand?"
  - Reward deck building that enables 1-2 hand wins
""")


if __name__ == "__main__":
    main()
