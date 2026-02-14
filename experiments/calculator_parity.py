"""
Experiment 3: Calculator Parity Analysis

Analyzes how often Calculator gives Chips (even sum) vs Mult (odd sum),
whether one outcome is dramatically better, and how hand type correlates
with parity.

Usage:
    python experiments/calculator_parity.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring_model import (
    Card, Rank, Suit, HandType, HAND_NAMES,
    make_deck, detect_hand, best_play, best_play_fast, score_hand,
    hand_base_score, Calculator,
)
from itertools import combinations
from collections import defaultdict
import random


def exhaustive_5card_analysis():
    """
    Enumerate ALL C(52,5) = 2,598,960 possible 5-card hands.
    For each, detect hand type, compute rank sum parity, and track stats.
    """
    print("=" * 70)
    print("Exhaustive 5-Card Hand Parity Analysis")
    print("(All 2,598,960 combinations)")
    print("=" * 70)

    deck = make_deck()

    total = 0
    even_count = 0
    odd_count = 0

    # Track per hand type
    ht_even = defaultdict(int)
    ht_odd = defaultdict(int)
    ht_even_sum = defaultdict(int)
    ht_odd_sum = defaultdict(int)
    ht_count = defaultdict(int)

    for combo in combinations(deck, 5):
        cards = list(combo)
        ht, scoring = detect_hand(cards)
        rank_sum = sum(c.rank_value for c in scoring)

        total += 1
        ht_count[ht] += 1

        if rank_sum % 2 == 0:
            even_count += 1
            ht_even[ht] += 1
            ht_even_sum[ht] += rank_sum
        else:
            odd_count += 1
            ht_odd[ht] += 1
            ht_odd_sum[ht] += rank_sum // 2

    print(f"\n  Total hands: {total:,}")
    print(f"  Even (Chips mode): {even_count:,} ({even_count/total*100:.1f}%)")
    print(f"  Odd (Mult mode):   {odd_count:,} ({odd_count/total*100:.1f}%)")

    print(f"\n  {'Hand Type':<20} {'Count':>8} {'Even%':>6} {'Odd%':>6} "
          f"{'Avg Chip+':>9} {'Avg Mult+':>9}")
    print(f"  {'-' * 65}")

    for ht in sorted(ht_count.keys()):
        count = ht_count[ht]
        ev = ht_even[ht]
        od = ht_odd[ht]
        ev_pct = ev / count * 100 if count else 0
        od_pct = od / count * 100 if count else 0
        avg_chip = ht_even_sum[ht] / ev if ev > 0 else 0
        avg_mult = ht_odd_sum[ht] / od if od > 0 else 0
        print(f"  {HAND_NAMES.get(ht, str(ht)):<20} {count:>8,} "
              f"{ev_pct:>5.1f}% {od_pct:>5.1f}% "
              f"{avg_chip:>9.1f} {avg_mult:>9.1f}")


def scoring_impact_analysis():
    """
    For each hand type, compare the actual score impact of Calculator in
    Chips mode vs Mult mode.
    """
    print("\n" + "=" * 70)
    print("Calculator Score Impact: Chips Mode vs Mult Mode")
    print("=" * 70)

    deck = make_deck()
    random.seed(42)

    # Sample 50,000 random 5-card hands
    n_samples = 50000
    even_scores = defaultdict(list)  # ht → [score deltas]
    odd_scores = defaultdict(list)

    calc = Calculator()

    for _ in range(n_samples):
        d = list(deck)
        random.shuffle(d)
        cards = d[:5]
        ht, scoring = detect_hand(cards)
        rank_sum = sum(c.rank_value for c in scoring)

        # Score without Calculator
        base_score, _, _ = score_hand(cards)

        # Score with Calculator
        calc_score, _, _ = score_hand(cards, jokers=[calc])

        delta = calc_score - base_score

        if rank_sum % 2 == 0:
            even_scores[ht].append(delta)
        else:
            odd_scores[ht].append(delta)

    print(f"\n  ({n_samples:,} random hands)")
    print(f"\n  {'Hand Type':<20} {'Even Avg Δ':>10} {'Odd Avg Δ':>10} "
          f"{'Even Count':>10} {'Odd Count':>10} {'Better Mode':>11}")
    print(f"  {'-' * 75}")

    for ht in sorted(set(list(even_scores.keys()) + list(odd_scores.keys()))):
        ev_deltas = even_scores.get(ht, [])
        od_deltas = odd_scores.get(ht, [])
        ev_avg = sum(ev_deltas) / len(ev_deltas) if ev_deltas else 0
        od_avg = sum(od_deltas) / len(od_deltas) if od_deltas else 0
        better = "Chips" if ev_avg > od_avg else "Mult" if od_avg > ev_avg else "Tied"
        print(f"  {HAND_NAMES.get(ht, str(ht)):<20} {ev_avg:>+10.1f} {od_avg:>+10.1f} "
              f"{len(ev_deltas):>10,} {len(od_deltas):>10,} {better:>11}")


def rank_value_sensitivity():
    """
    Test Calculator with A=14 vs A=11 to see which creates better balance.
    """
    print("\n" + "=" * 70)
    print("Rank Value Sensitivity: A=14 (design) vs A=11 (chip-based)")
    print("=" * 70)

    deck = make_deck()
    random.seed(42)
    n_samples = 50000

    # A=14 stats
    even_14 = 0
    odd_14 = 0
    sum_even_14 = 0
    sum_odd_14 = 0

    # A=11 stats
    even_11 = 0
    odd_11 = 0

    for _ in range(n_samples):
        d = list(deck)
        random.shuffle(d)
        cards = d[:5]
        _, scoring = detect_hand(cards)

        # A=14 (rank_value)
        sum_14 = sum(c.rank_value for c in scoring)
        if sum_14 % 2 == 0:
            even_14 += 1
            sum_even_14 += sum_14
        else:
            odd_14 += 1
            sum_odd_14 += sum_14 // 2

        # A=11 (chip_value-based ranking: A=11)
        sum_11 = sum((11 if c.rank == Rank.ACE else c.rank_value) for c in scoring)
        if sum_11 % 2 == 0:
            even_11 += 1
        else:
            odd_11 += 1

    print(f"\n  A=14 (design):  Even={even_14/n_samples*100:.1f}%  "
          f"Odd={odd_14/n_samples*100:.1f}%")
    print(f"  A=11 (alt):     Even={even_11/n_samples*100:.1f}%  "
          f"Odd={odd_11/n_samples*100:.1f}%")

    avg_chip_bonus = sum_even_14 / even_14 if even_14 else 0
    avg_mult_bonus = sum_odd_14 / odd_14 if odd_14 else 0
    print(f"\n  With A=14:")
    print(f"    Average Chips bonus (even): +{avg_chip_bonus:.1f}")
    print(f"    Average Mult bonus (odd):   +{avg_mult_bonus:.1f}")


def parity_manipulation():
    """
    Analyze how easily a player can manipulate parity by choosing which cards to play.
    From 8-card hands, compare best-hand parity vs what's achievable by picking cards.
    """
    print("\n" + "=" * 70)
    print("Parity Manipulation: Can Players Control Even/Odd?")
    print("=" * 70)

    deck = make_deck()
    random.seed(42)
    n_samples = 10000

    can_get_even = 0
    can_get_odd = 0
    can_get_both = 0
    best_is_even = 0

    for _ in range(n_samples):
        d = list(deck)
        random.shuffle(d)
        hand = d[:8]

        # Find best play
        ht_best, played_best, scoring_best = best_play(hand)
        best_sum = sum(c.rank_value for c in scoring_best)
        if best_sum % 2 == 0:
            best_is_even += 1

        # Check ALL 5-card combos for achievable parities
        has_even = False
        has_odd = False
        for combo in combinations(hand, 5):
            played = list(combo)
            _, scoring = detect_hand(played)
            rsum = sum(c.rank_value for c in scoring)
            if rsum % 2 == 0:
                has_even = True
            else:
                has_odd = True
            if has_even and has_odd:
                break

        if has_even:
            can_get_even += 1
        if has_odd:
            can_get_odd += 1
        if has_even and has_odd:
            can_get_both += 1

    print(f"\n  From 8-card hands ({n_samples:,} samples):")
    print(f"    Best play is even: {best_is_even/n_samples*100:.1f}%")
    print(f"    Can achieve even:  {can_get_even/n_samples*100:.1f}%")
    print(f"    Can achieve odd:   {can_get_odd/n_samples*100:.1f}%")
    print(f"    Can choose either: {can_get_both/n_samples*100:.1f}%")
    print(f"\n  Interpretation: If players can choose either parity {can_get_both/n_samples*100:.0f}% "
          f"of the time,")
    print(f"  Calculator creates meaningful decisions without feel-bad randomness.")


def main():
    exhaustive_5card_analysis()
    scoring_impact_analysis()
    rank_value_sensitivity()
    parity_manipulation()

    print("\n" + "=" * 70)
    print("KEY FINDINGS:")
    print("=" * 70)
    print("""
  Questions answered:
  1. Is the even/odd split close to 50/50?
  2. Is one mode (Chips vs Mult) dramatically better?
  3. Does hand type correlate with parity?
  4. Can players manipulate parity by choosing cards?
  5. Is A=14 or A=11 better for balance?

  If split is far from 50/50, consider:
  - Adjusting which ranks count as what value
  - Changing the bonus formula (e.g., sum/2 for chips, sum/3 for mult)
  - Using a different split criterion
""")


if __name__ == "__main__":
    main()
