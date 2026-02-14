"""
Experiment 2: Individual Joker Expected Value

For each of 14 candidate jokers, compute average score contribution per hand
across a simulated run. Compares to no-joker baseline to measure each joker's
effective power at each Ante.

Usage:
    python experiments/joker_ev.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring_model import (
    HandType, HAND_NAMES, make_deck, best_play_fast, score_hand,
    BLIND_SCORES, ALL_JOKERS, Card, Rank, Suit,
    ScoringContext,
)
import random
from collections import defaultdict


# Expected hand level by Ante
EXPECTED_LEVELS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5}
RARITY_NAMES = {1: "Common", 2: "Uncommon", 3: "Rare", 4: "Legendary"}

N_SAMPLES = 2000
HANDS_PER_BLIND = 4
ROUNDS_PER_ANTE = 3  # Small, Big, Boss


def simulate_joker_ev(joker_cls, ante, n_samples=N_SAMPLES):
    """
    Simulate n hands with a joker and without, returning (avg_with, avg_without).
    For stateful jokers, simulate a sequence of hands to accumulate state.
    """
    level = EXPECTED_LEVELS[ante]
    levels = {ht: level for ht in HandType}
    deck = make_deck()

    # Simulate state accumulation: by this Ante, the joker has been active
    # for (ante-1) * rounds_per_ante * hands_per_blind hands
    # Cap warmup to keep simulation fast
    hands_before = min((ante - 1) * ROUNDS_PER_ANTE * HANDS_PER_BLIND, 20)
    total_cards_before = hands_before * 5  # ~5 cards per hand

    scores_with = []
    scores_without = []

    for _ in range(n_samples):
        joker = joker_cls()
        joker.reset()

        # Warm up stateful jokers by simulating prior hands
        last_ht = None
        for h in range(hands_before):
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
                ante=max(1, ante - 1),
            )
            joker.on_hand_played(ctx)
            if (h + 1) % HANDS_PER_BLIND == 0:
                joker.on_round_end(ctx)
            last_ht = ht

        # Now score the actual test hand
        d = list(deck)
        random.shuffle(d)
        hand = d[:8]
        ht, played, scoring = best_play_fast(hand)

        # Score with joker
        score_j, _, _ = score_hand(
            played, jokers=[joker], hand_levels=levels,
            hands_remaining=2,
            hand_number_in_blind=2,
            round_number=hands_before // HANDS_PER_BLIND + 1,
            total_cards_played=total_cards_before,
            last_hand_type=last_ht,
            ante=ante,
        )

        # Score without joker
        score_base, _, _ = score_hand(
            played, jokers=[], hand_levels=levels,
        )

        scores_with.append(score_j)
        scores_without.append(score_base)

    avg_with = sum(scores_with) / len(scores_with)
    avg_without = sum(scores_without) / len(scores_without)
    return avg_with, avg_without


def main():
    random.seed(42)

    print("=" * 80)
    print("Experiment 2: Individual Joker Expected Value")
    print(f"({N_SAMPLES} samples per Ante per joker)")
    print("=" * 80)

    # Collect results for all jokers across all Antes
    results = {}  # joker_name → {ante → (avg_with, avg_without)}

    for joker_cls in ALL_JOKERS:
        joker_name = joker_cls.name
        rarity = joker_cls.rarity
        results[joker_name] = {"rarity": rarity}

        for ante in range(1, 9):
            avg_with, avg_without = simulate_joker_ev(joker_cls, ante)
            results[joker_name][ante] = (avg_with, avg_without)

    # Print results table for each joker
    for joker_cls in ALL_JOKERS:
        name = joker_cls.name
        rarity = RARITY_NAMES[joker_cls.rarity]
        data = results[name]

        print(f"\n{'─' * 80}")
        print(f"  {name} ({rarity}, ${joker_cls.cost})")
        print(f"{'─' * 80}")
        print(f"  {'Ante':>4}  {'Baseline':>10}  {'With Joker':>10}  "
              f"{'Delta':>10}  {'Boost %':>8}  {'Boss Req':>10}  {'% of Boss':>9}")

        for ante in range(1, 9):
            avg_with, avg_without = data[ante]
            delta = avg_with - avg_without
            boost_pct = (delta / avg_without * 100) if avg_without > 0 else 0
            boss_req = BLIND_SCORES["Boss"][ante - 1]
            pct_of_boss = (avg_with / boss_req * 100) if boss_req > 0 else 0
            print(f"  {ante:>4}  {avg_without:>10,.0f}  {avg_with:>10,.0f}  "
                  f"{delta:>+10,.0f}  {boost_pct:>+7.1f}%  "
                  f"{boss_req:>10,}  {pct_of_boss:>8.1f}%")

    # Summary comparison table
    print(f"\n{'=' * 80}")
    print("SUMMARY: Average Boost % by Ante")
    print(f"{'=' * 80}")
    print(f"  {'Joker':<20} {'R':>1}  ", end="")
    for ante in range(1, 9):
        print(f"{'A' + str(ante):>7}", end="")
    print(f"  {'Avg':>7}")
    print(f"  {'-' * 78}")

    for joker_cls in ALL_JOKERS:
        name = joker_cls.name
        rarity = joker_cls.rarity
        data = results[name]
        print(f"  {name:<20} {rarity:>1}  ", end="")
        boosts = []
        for ante in range(1, 9):
            avg_with, avg_without = data[ante]
            boost = ((avg_with - avg_without) / avg_without * 100) if avg_without > 0 else 0
            boosts.append(boost)
            print(f"{boost:>+6.0f}%", end="")
        avg_boost = sum(boosts) / len(boosts)
        print(f"  {avg_boost:>+6.0f}%")

    # Ranking by average boost
    print(f"\n{'=' * 80}")
    print("RANKING: Jokers by Average Score Boost")
    print(f"{'=' * 80}")

    ranking = []
    for joker_cls in ALL_JOKERS:
        name = joker_cls.name
        data = results[name]
        boosts = []
        for ante in range(1, 9):
            avg_with, avg_without = data[ante]
            boost = ((avg_with - avg_without) / avg_without * 100) if avg_without > 0 else 0
            boosts.append(boost)
        avg_boost = sum(boosts) / len(boosts)
        ranking.append((name, joker_cls.rarity, avg_boost))

    ranking.sort(key=lambda x: x[2], reverse=True)
    for i, (name, rarity, boost) in enumerate(ranking, 1):
        rarity_name = RARITY_NAMES[rarity]
        print(f"  {i:>2}. {name:<20} ({rarity_name:<9})  avg boost: {boost:>+.1f}%")

    # Target analysis
    print(f"\n{'=' * 80}")
    print("ANALYSIS: Does each rarity hit its target?")
    print(f"{'=' * 80}")
    print("""
  Target contribution by rarity:
    Common:    +10-30% boost
    Uncommon:  +20-50% boost
    Rare:      +40-80% boost (including xmult)
    Legendary: qualitative (not measurable by score boost alone)
""")
    for name, rarity, boost in ranking:
        rarity_name = RARITY_NAMES[rarity]
        if rarity == 1:
            target = "10-30%"
            in_range = 10 <= boost <= 30
        elif rarity == 2:
            target = "20-50%"
            in_range = 20 <= boost <= 50
        elif rarity == 3:
            target = "40-80%"
            in_range = 40 <= boost <= 80
        else:
            target = "N/A"
            in_range = True

        status = "OK" if in_range else ("LOW" if boost < 10 else "HIGH")
        print(f"  {name:<20} ({rarity_name:<9})  {boost:>+6.1f}%  "
              f"target: {target:<8}  [{status}]")


if __name__ == "__main__":
    main()
