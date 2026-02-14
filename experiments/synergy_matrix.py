"""
Experiment 7: Synergy Matrix

Measures pairwise synergy between all PhoneDeck jokers. Computes
synergy_ratio = score(i+j) / (score(i) + score(j) - score(baseline))
to identify super-linear combos and anti-synergies.

Usage:
    python experiments/synergy_matrix.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring_model import (
    HandType, HAND_NAMES, make_deck, best_play_fast, score_hand,
    ALL_JOKERS, ScoringContext, Card, Rank, Suit,
)
import random
from collections import defaultdict


N_SAMPLES = 1500
# Use mid-game Ante for synergy testing
TEST_ANTE = 4
TEST_LEVEL = 2
HANDS_PER_BLIND = 4
WARMUP_HANDS = 15  # Hands of state warmup for scaling jokers


def warmup_joker(joker, deck, levels):
    """Simulate prior hands to warm up stateful jokers."""
    last_ht = None
    for h in range(WARMUP_HANDS):
        d = list(deck)
        random.shuffle(d)
        hand = d[:8]
        ht, played, scoring = best_play_fast(hand)
        ctx = ScoringContext(
            hand_type=ht,
            scoring_cards=scoring,
            played_cards=played,
            hand_levels=levels,
            hands_remaining=HANDS_PER_BLIND - (h % HANDS_PER_BLIND) - 1,
            hand_number_in_blind=(h % HANDS_PER_BLIND) + 1,
            round_number=h // HANDS_PER_BLIND + 1,
            total_cards_played=h * 5,
            last_hand_type=last_ht,
            ante=TEST_ANTE,
        )
        joker.on_hand_played(ctx)
        if (h + 1) % HANDS_PER_BLIND == 0:
            joker.on_round_end(ctx)
        last_ht = ht
    return last_ht


def score_with_jokers(jokers, deck, levels, n_samples=N_SAMPLES):
    """Score n random hands with given jokers. Returns average score."""
    total = 0
    for _ in range(n_samples):
        d = list(deck)
        random.shuffle(d)
        hand = d[:8]
        _, played, scoring = best_play_fast(hand)
        score, _, _ = score_hand(
            played, jokers=jokers, hand_levels=levels,
            hands_remaining=2,
            hand_number_in_blind=2,
            total_cards_played=WARMUP_HANDS * 5,
            ante=TEST_ANTE,
        )
        total += score
    return total / n_samples


def compute_synergy_matrix():
    """Compute pairwise synergy ratios for all joker pairs."""
    deck = make_deck()
    levels = {ht: TEST_LEVEL for ht in HandType}

    joker_classes = ALL_JOKERS
    n = len(joker_classes)

    # Compute baseline (no jokers)
    baseline = score_with_jokers([], deck, levels)
    print(f"  Baseline (no jokers): {baseline:,.0f}")

    # Compute individual joker scores
    individual = {}
    for cls in joker_classes:
        joker = cls()
        joker.reset()
        warmup_joker(joker, deck, levels)
        avg = score_with_jokers([joker], deck, levels)
        individual[cls.name] = avg
        boost = (avg - baseline) / baseline * 100 if baseline > 0 else 0
        print(f"  {cls.name:<20}: {avg:>10,.0f} ({boost:>+.1f}%)")

    # Compute pairwise scores and synergy ratios
    matrix = {}
    for i, cls_i in enumerate(joker_classes):
        for j, cls_j in enumerate(joker_classes):
            if j <= i:
                continue  # Skip diagonal and lower triangle

            joker_i = cls_i()
            joker_j = cls_j()
            joker_i.reset()
            joker_j.reset()
            warmup_joker(joker_i, deck, levels)
            warmup_joker(joker_j, deck, levels)

            pair_score = score_with_jokers([joker_i, joker_j], deck, levels)

            # Synergy ratio: how does the pair compare to sum of individual contributions?
            # score(i+j) / (score(i) + score(j) - baseline)
            expected_additive = individual[cls_i.name] + individual[cls_j.name] - baseline
            if expected_additive > 0:
                ratio = pair_score / expected_additive
            else:
                ratio = 1.0

            matrix[(cls_i.name, cls_j.name)] = {
                "pair_score": pair_score,
                "expected": expected_additive,
                "ratio": ratio,
            }

    return baseline, individual, matrix


def main():
    random.seed(42)

    print("=" * 70)
    print("Experiment 7: Synergy Matrix")
    print(f"(Ante {TEST_ANTE}, Level {TEST_LEVEL}, {N_SAMPLES:,} samples per pair)")
    print("=" * 70)

    print("\nIndividual Joker Scores:")
    baseline, individual, matrix = compute_synergy_matrix()

    # Print full matrix
    names = [cls.name for cls in ALL_JOKERS]
    short_names = [n[:8] for n in names]

    print(f"\n{'=' * 70}")
    print("Synergy Ratio Matrix (ratio > 1.0 = super-linear synergy)")
    print(f"{'=' * 70}")

    # Print header
    print(f"\n  {'':>20}", end="")
    for sn in short_names:
        print(f" {sn:>8}", end="")
    print()
    print(f"  {'':>20}", end="")
    print("-" * (9 * len(short_names)))

    for i, name_i in enumerate(names):
        print(f"  {name_i:>20}", end="")
        for j, name_j in enumerate(names):
            if j <= i:
                print(f" {'---':>8}", end="")
            else:
                key = (name_i, name_j)
                if key in matrix:
                    ratio = matrix[key]["ratio"]
                    # Color-code: highlight strong synergies/anti-synergies
                    if ratio > 1.3:
                        marker = "**"
                    elif ratio < 0.7:
                        marker = "!!"
                    else:
                        marker = "  "
                    print(f" {ratio:>5.2f}{marker}", end="")
                else:
                    print(f" {'N/A':>8}", end="")
        print()

    # Top synergies
    print(f"\n{'=' * 70}")
    print("TOP 10 SYNERGY PAIRS (highest ratio)")
    print(f"{'=' * 70}")

    ranked = sorted(matrix.items(), key=lambda x: x[1]["ratio"], reverse=True)
    for i, ((n1, n2), data) in enumerate(ranked[:10], 1):
        print(f"  {i:>2}. {n1:>20} + {n2:<20}  ratio: {data['ratio']:.2f}  "
              f"pair: {data['pair_score']:>8,.0f}  expected: {data['expected']:>8,.0f}")

    # Worst anti-synergies
    print(f"\n{'=' * 70}")
    print("WORST 5 ANTI-SYNERGY PAIRS (lowest ratio)")
    print(f"{'=' * 70}")

    for i, ((n1, n2), data) in enumerate(ranked[-5:], 1):
        print(f"  {i:>2}. {n1:>20} + {n2:<20}  ratio: {data['ratio']:.2f}  "
              f"pair: {data['pair_score']:>8,.0f}  expected: {data['expected']:>8,.0f}")

    # Check intended synergies
    print(f"\n{'=' * 70}")
    print("INTENDED SYNERGY CHECK")
    print(f"{'=' * 70}")

    intended = [
        ("Camera", "Playlist", "Both reward same-hand-type play"),
        ("Alarm Clock", "Doom Scrolling", "Doom loses discards → more pressure on last hand"),
        ("Battery", "Timer", "Both reward efficiency"),
        ("Calculator", "Flashlight", "High first-card chips + Calculator's chip mode"),
    ]

    for n1, n2, reason in intended:
        key = (n1, n2) if (n1, n2) in matrix else (n2, n1)
        if key in matrix:
            data = matrix[key]
            status = "CONFIRMED" if data["ratio"] > 1.1 else "WEAK" if data["ratio"] > 1.0 else "MISSING"
            print(f"  [{status:>9}] {n1} + {n2}: ratio {data['ratio']:.2f}")
            print(f"             Reason: {reason}")
        else:
            print(f"  [NOT FOUND] {n1} + {n2}")

    # Check intended anti-synergies
    print(f"\n{'=' * 70}")
    print("INTENDED ANTI-SYNERGY CHECK")
    print(f"{'=' * 70}")

    anti = [
        ("Alarm Clock", "Battery", "Alarm wants all hands used, Battery wants hands saved"),
        ("Timer", "Alarm Clock", "Timer wants hands saved, Alarm wants last hand used"),
    ]

    for n1, n2, reason in anti:
        key = (n1, n2) if (n1, n2) in matrix else (n2, n1)
        if key in matrix:
            data = matrix[key]
            status = "CONFIRMED" if data["ratio"] < 0.9 else "WEAK" if data["ratio"] < 1.0 else "MISSING"
            print(f"  [{status:>9}] {n1} + {n2}: ratio {data['ratio']:.2f}")
            print(f"             Reason: {reason}")

    print(f"\n{'=' * 70}")
    print("KEY FINDINGS:")
    print(f"{'=' * 70}")
    print("""
  Success criteria:
  - Several pairs with ratio > 1.3 (super-linear combos)
  - No unintentional pairs with ratio < 0.7
  - Intended synergies (Camera+Playlist, Alarm+DoomScrolling) show up as hot spots
  - Intended anti-synergies (AlarmClock+Battery) show up as cold spots

  If a joker doesn't synergize with anything, it's a cut candidate.
  If two jokers synergize with everything the same way, one may be redundant.
""")


if __name__ == "__main__":
    main()
