"""
Experiment 1: Ante Score Requirements Curve

Models the score needed to beat each blind at each Ante (1-8).
Calculates what hand + joker combos are needed at each stage.
Establishes target power levels for PhoneDeck jokers.

Usage:
    python experiments/ante_curve.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring_model import (
    BLIND_SCORES, HandType, HAND_NAMES, hand_base_score,
    make_deck, best_play_fast, score_hand, Card, Rank, Suit,
    simulate_hands,
)
import random


def print_blind_table():
    """Print the full Ante × Blind score requirement table."""
    print("=" * 70)
    print("Ante Score Requirements (Base Stake)")
    print("=" * 70)
    print(f"{'Ante':>4}  {'Small':>8}  {'Big':>8}  {'Boss':>8}  {'Growth':>8}")
    print("-" * 70)

    prev_boss = None
    for ante in range(1, 9):
        small = BLIND_SCORES["Small"][ante - 1]
        big = BLIND_SCORES["Big"][ante - 1]
        boss = BLIND_SCORES["Boss"][ante - 1]
        growth = f"{boss / prev_boss:.1f}x" if prev_boss else "-"
        print(f"{ante:>4}  {small:>8,}  {big:>8,}  {boss:>8,}  {growth:>8}")
        prev_boss = boss


def analyze_hand_power_by_ante():
    """Show what each hand type scores at different levels across antes."""
    print("\n" + "=" * 70)
    print("Hand Type Scoring by Level (no jokers)")
    print("=" * 70)

    # Representative hands for each type with typical card values
    # We show base + typical card chips
    hand_types_to_show = [
        HandType.HIGH_CARD,
        HandType.PAIR,
        HandType.TWO_PAIR,
        HandType.THREE_OF_A_KIND,
        HandType.STRAIGHT,
        HandType.FLUSH,
        HandType.FULL_HOUSE,
        HandType.FOUR_OF_A_KIND,
        HandType.STRAIGHT_FLUSH,
    ]

    # Typical card chip contribution per hand type (estimated)
    typical_card_chips = {
        HandType.HIGH_CARD: 11,        # Ace
        HandType.PAIR: 22,             # Pair of Aces
        HandType.TWO_PAIR: 42,         # Aces + Kings
        HandType.THREE_OF_A_KIND: 33,  # Three Aces
        HandType.STRAIGHT: 42,         # 10-A straight
        HandType.FLUSH: 38,            # Average flush
        HandType.FULL_HOUSE: 40,       # Kings full of 5s
        HandType.FOUR_OF_A_KIND: 40,   # Four 10s
        HandType.STRAIGHT_FLUSH: 42,   # 10-A suited
    }

    for level in [1, 3, 5]:
        print(f"\n  Level {level}:")
        print(f"  {'Hand Type':<20} {'Base C':>7} {'Base M':>7} "
              f"{'+ Cards':>7} {'Score':>10}")
        print(f"  {'-' * 55}")

        for ht in hand_types_to_show:
            base_c, base_m = hand_base_score(ht, level)
            card_c = typical_card_chips[ht]
            total = (base_c + card_c) * base_m
            print(f"  {HAND_NAMES[ht]:<20} {base_c:>7,} {base_m:>7} "
                  f"{card_c:>7} {total:>10,}")


def power_curve_analysis():
    """For each Ante, show which hand types (at expected levels) can beat each blind."""
    print("\n" + "=" * 70)
    print("Can This Hand Beat The Blind? (single hand, no jokers)")
    print("=" * 70)

    # Expected hand level by Ante (rough: planet cards level up ~1 hand per ante)
    # Most players focus on 1-2 hand types
    expected_levels = {
        1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5
    }

    # Typical card chip values per hand type
    typical_card_chips = {
        HandType.PAIR: 22,
        HandType.TWO_PAIR: 42,
        HandType.THREE_OF_A_KIND: 33,
        HandType.STRAIGHT: 42,
        HandType.FLUSH: 38,
        HandType.FULL_HOUSE: 40,
        HandType.FOUR_OF_A_KIND: 40,
        HandType.STRAIGHT_FLUSH: 42,
    }

    for ante in range(1, 9):
        boss_req = BLIND_SCORES["Boss"][ante - 1]
        level = expected_levels[ante]
        print(f"\n  Ante {ante} (Boss: {boss_req:>8,}, hand level ~{level}):")

        for ht in [HandType.PAIR, HandType.FLUSH, HandType.FULL_HOUSE,
                    HandType.FOUR_OF_A_KIND, HandType.STRAIGHT_FLUSH]:
            base_c, base_m = hand_base_score(ht, level)
            card_c = typical_card_chips[ht]
            score = (base_c + card_c) * base_m
            ratio = score / boss_req
            status = "YES" if score >= boss_req else f"need {ratio:.0%}"
            print(f"    {HAND_NAMES[ht]:<20} = {score:>8,}  {status}")


def joker_power_targets():
    """
    Calculate how much joker contribution is needed to bridge the gap between
    hand scores and blind requirements.
    """
    print("\n" + "=" * 70)
    print("Joker Power Budget: How Much Must Jokers Contribute?")
    print("=" * 70)
    print("(Assuming 4 hands per blind, focused hand type, planet leveling)")

    expected_levels = {
        1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5
    }

    # Assume player focuses on Pair (common) and Full House (strong)
    for focus_ht, focus_name in [(HandType.PAIR, "Pair"), (HandType.FULL_HOUSE, "Full House")]:
        print(f"\n  Focus: {focus_name}")
        print(f"  {'Ante':>4}  {'Blind':>8}  {'Hand Score':>10}  "
              f"{'4-Hand Total':>12}  {'Gap':>10}  {'Mult Needed':>11}")
        print(f"  {'-' * 65}")

        typical_card_chips = {HandType.PAIR: 22, HandType.FULL_HOUSE: 40}

        for ante in range(1, 9):
            boss_req = BLIND_SCORES["Boss"][ante - 1]
            level = expected_levels[ante]
            base_c, base_m = hand_base_score(focus_ht, level)
            card_c = typical_card_chips[focus_ht]
            hand_score = (base_c + card_c) * base_m
            four_hands = hand_score * 4
            gap = max(0, boss_req - four_hands)
            # What xmult would be needed to bridge the gap with 4 hands?
            mult_needed = boss_req / four_hands if four_hands > 0 else float('inf')
            gap_str = f"{gap:>10,}" if gap > 0 else "    --"
            print(f"  {ante:>4}  {boss_req:>8,}  {hand_score:>10,}  "
                  f"{four_hands:>12,}  {gap_str}  {mult_needed:>10.1f}x")


def monte_carlo_baseline():
    """
    Run Monte Carlo simulations of random hands to establish baseline scores.
    """
    print("\n" + "=" * 70)
    print("Monte Carlo Baseline: Average Score Per Hand (no jokers, 5000 samples)")
    print("=" * 70)

    random.seed(42)
    expected_levels = {
        1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5
    }

    print(f"\n  {'Ante':>4}  {'Level':>5}  {'Avg Score':>10}  {'Median':>10}  "
          f"{'Max':>10}  {'Boss Req':>10}  {'Hands Needed':>12}")
    print(f"  {'-' * 75}")

    for ante in range(1, 9):
        level = expected_levels[ante]
        levels = {ht: level for ht in HandType}
        results = simulate_hands(n=5000, hand_levels=levels)
        scores = [r[0] for r in results]
        scores.sort()
        avg = sum(scores) / len(scores)
        median = scores[len(scores) // 2]
        mx = max(scores)
        boss_req = BLIND_SCORES["Boss"][ante - 1]
        hands_needed = boss_req / avg if avg > 0 else float('inf')
        print(f"  {ante:>4}  {level:>5}  {avg:>10,.0f}  {median:>10,}  "
              f"{mx:>10,}  {boss_req:>10,}  {hands_needed:>11.1f}")


def main():
    print_blind_table()
    analyze_hand_power_by_ante()
    power_curve_analysis()
    joker_power_targets()
    monte_carlo_baseline()

    print("\n" + "=" * 70)
    print("KEY FINDINGS:")
    print("=" * 70)
    print("""
  - Blind scores grow ~2-2.7x per Ante (exponential)
  - By Ante 5+, no single hand can beat Boss blind without jokers
  - Joker multipliers become essential from Ante 3 onward
  - Common jokers should provide ~1.5-2x effective multiplier
  - Rare jokers should provide ~3-5x effective multiplier
  - Legendary jokers should be transformative (enabling otherwise-impossible wins)

  Target joker contribution (as fraction of needed score):
    Common:    10-30% of gap at their Ante
    Uncommon:  20-50% of gap
    Rare:      40-80% of gap
    Legendary: qualitative game-changer
""")


if __name__ == "__main__":
    main()
