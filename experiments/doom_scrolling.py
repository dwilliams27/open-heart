"""
Experiment 8: Doom Scrolling Viability Window

Analyzes at what round Doom Scrolling's discard cost outweighs its Mult benefit.
Models the tradeoff between growing Mult bonus and shrinking discards.

Usage:
    python experiments/doom_scrolling.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring_model import (
    HandType, HAND_NAMES, make_deck, best_play_fast, best_play_with_discards,
    score_hand, BLIND_SCORES, DoomScrolling, hand_base_score,
)
import random
from collections import defaultdict


N_SIMULATIONS = 2000
EXPECTED_LEVELS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5}
BASE_DISCARDS = 3
HANDS_PER_BLIND = 4


def hand_quality_vs_discards():
    """
    Measure how hand quality (best achievable hand type + score) varies
    with number of available discards.
    """
    print("=" * 70)
    print("Hand Quality vs Discards Available")
    print(f"({N_SIMULATIONS:,} samples per discard count)")
    print("=" * 70)

    deck = make_deck()
    random.seed(42)
    level = 2
    levels = {ht: level for ht in HandType}

    print(f"\n  {'Discards':>8}  {'Avg Score':>10}  {'Avg Hand Type':>15}  "
          f"{'P(Flush+)':>10}  {'P(Pair-)':>10}")
    print(f"  {'-' * 60}")

    for num_discards in range(0, 5):
        scores = []
        hand_type_counts = defaultdict(int)

        for _ in range(N_SIMULATIONS):
            d = list(deck)
            random.shuffle(d)

            ht, played, scoring = best_play_with_discards(
                d, hand_size=8, play_size=5, num_discards=num_discards
            )
            score, _, _ = score_hand(played, hand_levels=levels)
            scores.append(score)
            hand_type_counts[ht] += 1

        avg_score = sum(scores) / len(scores)
        avg_ht = sum(int(ht) * c for ht, c in hand_type_counts.items()) / N_SIMULATIONS
        flush_plus = sum(c for ht, c in hand_type_counts.items() if ht >= HandType.FLUSH) / N_SIMULATIONS * 100
        pair_minus = sum(c for ht, c in hand_type_counts.items() if ht <= HandType.PAIR) / N_SIMULATIONS * 100

        ht_name = HAND_NAMES.get(HandType(round(avg_ht)), f"~{avg_ht:.1f}")
        print(f"  {num_discards:>8}  {avg_score:>10,.0f}  {ht_name:>15}  "
              f"{flush_plus:>9.1f}%  {pair_minus:>9.1f}%")


def doom_scrolling_timeline():
    """
    Model Doom Scrolling's state across an entire run.
    Track Mult bonus, discards remaining, and net impact.
    """
    print("\n" + "=" * 70)
    print("Doom Scrolling Timeline: Mult Bonus vs Discard Cost")
    print("=" * 70)

    print(f"\n  {'Round':>5}  {'Ante':>4}  {'DS Mult':>7}  {'Discards':>8}  "
          f"{'Lost':>4}  {'Status':>10}")
    print(f"  {'-' * 50}")

    doom = DoomScrolling()
    doom.reset()

    total_rounds = 8 * 3  # 8 Antes × 3 blinds
    for r in range(total_rounds):
        ante = r // 3 + 1
        blind = ["Small", "Big", "Boss"][r % 3]
        mult_bonus = doom.mult_bonus
        discards_remaining = max(0, BASE_DISCARDS - doom.discards_lost)

        if discards_remaining >= 2:
            status = "Healthy"
        elif discards_remaining == 1:
            status = "Risky"
        else:
            status = "DANGER"

        print(f"  {r+1:>5}  {ante:>4}  +{mult_bonus:>5}  {discards_remaining:>8}  "
              f"{doom.discards_lost:>4}  {status:>10}")

        doom.on_round_end(None)


def viability_simulation():
    """
    For each round in a run, simulate whether Doom Scrolling helps or hurts.
    Compare score WITH Doom Scrolling (mult bonus, fewer discards) vs
    WITHOUT (no bonus, full discards).
    """
    print("\n" + "=" * 70)
    print("Doom Scrolling Viability: Net Score Impact Per Round")
    print(f"({N_SIMULATIONS:,} simulations)")
    print("=" * 70)

    deck = make_deck()
    random.seed(42)

    print(f"\n  {'Round':>5}  {'Ante':>4}  {'No DS Avg':>10}  {'DS Avg':>10}  "
          f"{'Delta':>10}  {'Delta%':>8}  {'Verdict':>10}")
    print(f"  {'-' * 70}")

    doom = DoomScrolling()
    doom.reset()

    for r in range(24):  # 8 Antes × 3 blinds
        ante = r // 3 + 1
        level = EXPECTED_LEVELS[ante]
        levels = {ht: level for ht in HandType}
        discards_with_ds = max(0, BASE_DISCARDS - doom.discards_lost)

        scores_without = []
        scores_with = []

        for _ in range(N_SIMULATIONS):
            d = list(deck)
            random.shuffle(d)

            # WITHOUT Doom Scrolling: full discards, no mult bonus
            ht_no, played_no, scoring_no = best_play_with_discards(
                list(d), hand_size=8, num_discards=BASE_DISCARDS
            )
            score_no, _, _ = score_hand(played_no, hand_levels=levels)
            scores_without.append(score_no)

            # WITH Doom Scrolling: fewer discards, mult bonus from joker
            ht_ds, played_ds, scoring_ds = best_play_with_discards(
                list(d), hand_size=8, num_discards=discards_with_ds
            )
            score_ds, _, _ = score_hand(
                played_ds, jokers=[doom], hand_levels=levels
            )
            scores_with.append(score_ds)

        avg_no = sum(scores_without) / len(scores_without)
        avg_ds = sum(scores_with) / len(scores_with)
        delta = avg_ds - avg_no
        delta_pct = (delta / avg_no * 100) if avg_no > 0 else 0

        if delta > 0:
            verdict = "POSITIVE" if delta_pct > 10 else "marginal+"
        else:
            verdict = "NEGATIVE" if delta_pct < -10 else "marginal-"

        print(f"  {r+1:>5}  {ante:>4}  {avg_no:>10,.0f}  {avg_ds:>10,.0f}  "
              f"{delta:>+10,.0f}  {delta_pct:>+7.1f}%  {verdict:>10}")

        # Advance Doom Scrolling state
        doom.on_round_end(None)


def parameter_sweep():
    """Sweep Doom Scrolling parameters to find the sweet spot."""
    print("\n" + "=" * 70)
    print("Parameter Sweep: Optimal Doom Scrolling Values")
    print("=" * 70)
    print("  Target: positive through Ante 5-6, liability by Ante 7-8")

    deck = make_deck()
    level = 3  # Mid-game
    levels = {ht: level for ht in HandType}

    configs = [
        ("+3 mult/round", 3),
        ("+4 mult/round (design)", 4),
        ("+5 mult/round", 5),
        ("+6 mult/round", 6),
    ]

    print(f"\n  {'Config':<25}", end="")
    for r in range(1, 13):
        print(f" R{r:>2}", end="")
    print()
    print(f"  {'-' * 80}")

    random.seed(42)
    for name, mult_per_round in configs:
        print(f"  {name:<25}", end="")
        for r in range(1, 13):
            # At round r: mult bonus = mult_per_round * r, discards lost = r
            bonus = mult_per_round * r
            discards = max(0, BASE_DISCARDS - r)

            # Score 500 hands with/without
            scores_no = []
            scores_ds = []
            for _ in range(500):
                d = list(deck)
                random.shuffle(d)

                # Without
                ht_no, played_no, _ = best_play_with_discards(
                    list(d), num_discards=BASE_DISCARDS
                )
                score_no, _, _ = score_hand(played_no, hand_levels=levels)
                scores_no.append(score_no)

                # With (manual mult bonus)
                ht_ds, played_ds, _ = best_play_with_discards(
                    list(d), num_discards=discards
                )
                score_ds, ht_ds_actual, scoring_ds = score_hand(played_ds, hand_levels=levels)
                base_c, base_m = hand_base_score(ht_ds_actual, level)
                card_chips = sum(c.chip_value for c in scoring_ds)
                total_chips = base_c + card_chips
                total_mult = base_m + bonus
                score_ds_adjusted = total_chips * total_mult
                scores_ds.append(score_ds_adjusted)

            avg_no = sum(scores_no) / len(scores_no)
            avg_ds = sum(scores_ds) / len(scores_ds)
            if avg_ds > avg_no:
                indicator = "+"
            else:
                indicator = "-"
            print(f" {indicator:>3}", end="")
        print()


def sell_timing_analysis():
    """When should you sell Doom Scrolling to avoid the discard death spiral?"""
    print("\n" + "=" * 70)
    print("Sell Timing: When Does Doom Scrolling Become a Liability?")
    print("=" * 70)

    deck = make_deck()
    random.seed(42)

    print(f"\n  Simulating {N_SIMULATIONS} hands at each round state:")
    print(f"\n  {'Rounds Held':>11}  {'DS Mult':>7}  {'Discards':>8}  "
          f"{'Avg Score':>10}  {'vs Baseline':>11}  {'Recommendation':>15}")
    print(f"  {'-' * 70}")

    level = 3
    levels = {ht: level for ht in HandType}

    # Baseline: no doom scrolling, 3 discards
    baseline_scores = []
    for _ in range(N_SIMULATIONS):
        d = list(deck)
        random.shuffle(d)
        ht, played, _ = best_play_with_discards(list(d), num_discards=BASE_DISCARDS)
        score, _, _ = score_hand(played, hand_levels=levels)
        baseline_scores.append(score)
    baseline_avg = sum(baseline_scores) / len(baseline_scores)

    for rounds_held in range(0, 15):
        mult_bonus = 4 * rounds_held
        discards = max(0, BASE_DISCARDS - rounds_held)

        ds_scores = []
        for _ in range(N_SIMULATIONS):
            d = list(deck)
            random.shuffle(d)
            ht, played, scoring = best_play_with_discards(
                list(d), num_discards=discards
            )
            # Score with doom scrolling mult bonus
            score_raw, ht_actual, scoring_actual = score_hand(played, hand_levels=levels)
            base_c, base_m = hand_base_score(ht_actual, level)
            card_chips = sum(c.chip_value for c in scoring_actual)
            score_ds = (base_c + card_chips) * (base_m + mult_bonus)
            ds_scores.append(score_ds)

        ds_avg = sum(ds_scores) / len(ds_scores)
        delta_pct = (ds_avg - baseline_avg) / baseline_avg * 100

        if delta_pct > 20:
            rec = "KEEP (strong)"
        elif delta_pct > 5:
            rec = "KEEP (ok)"
        elif delta_pct > -5:
            rec = "SELL SOON"
        else:
            rec = "SELL NOW"

        print(f"  {rounds_held:>11}  +{mult_bonus:>5}  {discards:>8}  "
              f"{ds_avg:>10,.0f}  {delta_pct:>+10.1f}%  {rec:>15}")


def main():
    hand_quality_vs_discards()
    doom_scrolling_timeline()
    viability_simulation()
    sell_timing_analysis()

    print(f"\n{'=' * 70}")
    print("KEY FINDINGS:")
    print(f"{'=' * 70}")
    print("""
  Questions answered:
  1. At what round does the discard cost outweigh the Mult benefit?
  2. Is "sell before it kills you" a real decision?
  3. How much does hand quality degrade with fewer discards?
  4. Does +4 mult/round hit the sweet spot?

  Doom Scrolling should:
  - Feel powerful and tempting in early rounds (+4, +8, +12 Mult!)
  - Start feeling painful around round 4-5 (1 discard left)
  - Be clearly bad to hold past round 6+ (0 discards)
  - Create a genuine "I should sell this... but one more round..." feeling
  - Pair well with discard-granting jokers (extending viability)
""")


if __name__ == "__main__":
    main()
