"""
Experiment 4: Playlist Streak Probability

Simulates how often players can maintain same-hand-type streaks across
consecutive hands in a blind. Key question: is Playlist's XMult achievable
often enough to justify Rare rarity?

Usage:
    python experiments/playlist_streaks.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring_model import (
    Card, Rank, Suit, HandType, HAND_NAMES,
    make_deck, best_play_fast, best_play_with_discards,
    detect_hand, Playlist, score_hand,
)
import random
from collections import defaultdict


HANDS_PER_BLIND = 4
N_SIMULATIONS = 10000


def simulate_blind_streaks(hand_size=8, num_discards=3, n_sims=N_SIMULATIONS):
    """
    Simulate n blinds (4 hands each). For each blind:
    - Draw hand_size cards from a shuffled deck for each hand
    - Find best play
    - Track consecutive same-type streaks

    Returns streak length distribution and per-hand-type breakdown.
    """
    deck = make_deck()
    streak_counts = defaultdict(int)  # streak_length → count
    ht_streak_counts = defaultdict(lambda: defaultdict(int))  # ht → streak_length → count
    total_blinds = 0
    max_xmult_seen = 0

    for _ in range(n_sims):
        d = list(deck)
        random.shuffle(d)

        # Simulate 4 hands from the same shuffled deck
        # (In Balatro, you draw from the same deck across a blind)
        draw_pile = list(d)
        hand_types = []

        for h in range(HANDS_PER_BLIND):
            if len(draw_pile) < hand_size:
                # Deck exhausted, reshuffle (simplified)
                draw_pile = list(d)
                random.shuffle(draw_pile)

            hand = draw_pile[:hand_size]
            draw_pile = draw_pile[hand_size:]

            ht, played, scoring = best_play_fast(hand)
            hand_types.append(ht)

            # Remove played cards from the available pool
            # (simplification: we don't model drawing back up)

        # Count streaks
        current_streak = 1
        for i in range(1, len(hand_types)):
            if hand_types[i] == hand_types[i - 1]:
                current_streak += 1
            else:
                streak_counts[current_streak] += 1
                ht_streak_counts[hand_types[i - 1]][current_streak] += 1
                current_streak = 1
        streak_counts[current_streak] += 1
        ht_streak_counts[hand_types[-1]][current_streak] += 1

        # Calculate max Playlist XMult this blind would have produced
        current_streak = 0
        max_blind_xmult = 1.0
        prev_ht = None
        for ht in hand_types:
            if ht == prev_ht:
                current_streak += 1
            else:
                current_streak = 0
            xm = {0: 1.0, 1: 1.5, 2: 2.0}.get(current_streak, 2.5)
            max_blind_xmult = max(max_blind_xmult, xm)
            prev_ht = ht
        if max_blind_xmult > max_xmult_seen:
            max_xmult_seen = max_blind_xmult

        total_blinds += 1

    return streak_counts, ht_streak_counts, total_blinds


def simulate_with_strategy(n_sims=N_SIMULATIONS):
    """
    Simulate blinds where the player TRIES to maintain streaks.
    Strategy: after the first hand, try to play the same hand type.
    If the best hand is different, check if any 5-card combo matches the target.
    """
    deck = make_deck()
    streak_counts = defaultdict(int)
    total_blinds = 0

    for _ in range(n_sims):
        d = list(deck)
        random.shuffle(d)
        draw_pile = list(d)

        target_ht = None
        current_streak = 1
        hand_types = []

        for h in range(HANDS_PER_BLIND):
            if len(draw_pile) < 8:
                draw_pile = list(d)
                random.shuffle(draw_pile)

            hand = draw_pile[:8]
            draw_pile = draw_pile[8:]

            if target_ht is None:
                # First hand: play the best
                ht, played, scoring = best_play_fast(hand)
                target_ht = ht
            else:
                # Try to match target hand type
                ht_best, played_best, scoring_best = best_play_fast(hand)

                if ht_best == target_ht:
                    ht = ht_best
                else:
                    # Search for any 5-card combo that gives target type
                    found = False
                    from itertools import combinations as combos
                    for combo in combos(hand, 5):
                        test_ht, _ = detect_hand(list(combo))
                        if test_ht == target_ht:
                            ht = target_ht
                            found = True
                            break
                    if not found:
                        # Can't maintain streak, play best and reset
                        ht = ht_best
                        target_ht = ht
                        streak_counts[current_streak] += 1
                        current_streak = 0

                if ht == target_ht:
                    current_streak += 1
                else:
                    streak_counts[current_streak] += 1
                    current_streak = 1
                    target_ht = ht

            hand_types.append(ht)

        streak_counts[current_streak] += 1
        total_blinds += 1

    return streak_counts, total_blinds


def compute_playlist_ev(streak_counts, total_blinds):
    """Compute expected Playlist XMult per blind from streak distribution."""
    # For a 4-hand blind, the Playlist XMult sequence for a streak of length s is:
    # Hand 1: X1.0, Hand 2: X1.5, Hand 3: X2.0, Hand 4: X2.5
    # But only on hands 2+ of the streak
    # Average XMult = (1.0 + xmult values for hands in streak) / total hands

    # Simpler: compute total XMult "bonus hands" across all blinds
    total_xmult_sum = 0.0
    total_hands = total_blinds * HANDS_PER_BLIND

    # Each streak of length s contributes:
    # s=1: 0 bonus xmult hands
    # s=2: 1 hand at X1.5
    # s=3: 1 hand at X1.5 + 1 hand at X2.0
    # s=4: 1 hand at X1.5 + 1 hand at X2.0 + 1 hand at X2.5
    streak_xmult = {
        1: 0,
        2: 1.5,
        3: 1.5 + 2.0,
        4: 1.5 + 2.0 + 2.5,
    }

    for length, count in streak_counts.items():
        xm = streak_xmult.get(length, 0)
        if length > 4:
            xm = 1.5 + 2.0 + sum(2.5 for _ in range(length - 2))
        total_xmult_sum += xm * count

    avg_xmult_per_blind = total_xmult_sum / total_blinds if total_blinds > 0 else 0
    pct_hands_with_bonus = sum(
        max(0, length - 1) * count for length, count in streak_counts.items()
    ) / total_hands * 100

    return avg_xmult_per_blind, pct_hands_with_bonus


def main():
    random.seed(42)

    print("=" * 70)
    print("Experiment 4: Playlist Streak Probability")
    print(f"({N_SIMULATIONS:,} simulated blinds, {HANDS_PER_BLIND} hands each)")
    print("=" * 70)

    # --- Greedy play (best hand each time) ---
    print("\n--- Greedy Strategy (always play best hand) ---")
    streak_counts, ht_streaks, total = simulate_blind_streaks()

    total_streaks = sum(streak_counts.values())
    print(f"\n  Streak Length Distribution:")
    for length in sorted(streak_counts.keys()):
        count = streak_counts[length]
        pct = count / total_streaks * 100
        bar = "█" * int(pct)
        print(f"    Length {length}: {count:>6,} ({pct:>5.1f}%) {bar}")

    # P(streak >= N) for each N
    print(f"\n  P(streak >= N) within a 4-hand blind:")
    for min_streak in [2, 3, 4]:
        count = sum(c for l, c in streak_counts.items() if l >= min_streak)
        pct = count / total * 100
        print(f"    P(streak >= {min_streak}): {pct:.1f}% of blinds")

    ev_xmult, pct_bonus = compute_playlist_ev(streak_counts, total)
    print(f"\n  Average Playlist XMult bonus per blind: {ev_xmult:.2f}")
    print(f"  % of hands with streak bonus: {pct_bonus:.1f}%")

    # Per hand type breakdown
    print(f"\n  Per-Hand-Type Streak Rates:")
    print(f"  {'Hand Type':<20} {'Total':>6} {'Str2+':>6} {'Str3+':>6} {'Str4':>6}")
    print(f"  {'-' * 50}")

    for ht in sorted(ht_streaks.keys()):
        data = ht_streaks[ht]
        total_ht = sum(data.values())
        str2 = sum(c for l, c in data.items() if l >= 2)
        str3 = sum(c for l, c in data.items() if l >= 3)
        str4 = sum(c for l, c in data.items() if l >= 4)
        if total_ht > 50:  # Only show meaningful sample sizes
            print(f"  {HAND_NAMES.get(ht, str(ht)):<20} {total_ht:>6} "
                  f"{str2/total_ht*100:>5.1f}% {str3/total_ht*100:>5.1f}% "
                  f"{str4/total_ht*100:>5.1f}%")

    # --- Streak-seeking strategy ---
    print("\n\n--- Streak-Seeking Strategy (try to match previous hand type) ---")
    streak_counts_s, total_s = simulate_with_strategy()

    total_streaks_s = sum(streak_counts_s.values())
    print(f"\n  Streak Length Distribution:")
    for length in sorted(streak_counts_s.keys()):
        count = streak_counts_s[length]
        pct = count / total_streaks_s * 100
        bar = "█" * int(pct)
        print(f"    Length {length}: {count:>6,} ({pct:>5.1f}%) {bar}")

    print(f"\n  P(streak >= N) within a 4-hand blind:")
    for min_streak in [2, 3, 4]:
        count = sum(c for l, c in streak_counts_s.items() if l >= min_streak)
        pct = count / total_s * 100
        print(f"    P(streak >= {min_streak}): {pct:.1f}% of blinds")

    ev_xmult_s, pct_bonus_s = compute_playlist_ev(streak_counts_s, total_s)
    print(f"\n  Average Playlist XMult bonus per blind: {ev_xmult_s:.2f}")
    print(f"  % of hands with streak bonus: {pct_bonus_s:.1f}%")

    # --- Comparison ---
    print(f"\n{'=' * 70}")
    print("COMPARISON: Greedy vs Streak-Seeking")
    print(f"{'=' * 70}")
    print(f"  {'Metric':<35} {'Greedy':>10} {'Streak':>10} {'Delta':>10}")
    print(f"  {'-' * 65}")
    s2_g = sum(c for l, c in streak_counts.items() if l >= 2) / total * 100
    s2_s = sum(c for l, c in streak_counts_s.items() if l >= 2) / total_s * 100
    print(f"  {'P(streak >= 2)':<35} {s2_g:>9.1f}% {s2_s:>9.1f}% {s2_s-s2_g:>+9.1f}%")
    s3_g = sum(c for l, c in streak_counts.items() if l >= 3) / total * 100
    s3_s = sum(c for l, c in streak_counts_s.items() if l >= 3) / total_s * 100
    print(f"  {'P(streak >= 3)':<35} {s3_g:>9.1f}% {s3_s:>9.1f}% {s3_s-s3_g:>+9.1f}%")
    print(f"  {'Avg XMult bonus/blind':<35} {ev_xmult:>10.2f} {ev_xmult_s:>10.2f} "
          f"{ev_xmult_s-ev_xmult:>+10.2f}")

    # --- Vanilla xmult comparison ---
    print(f"\n{'=' * 70}")
    print("COMPARISON: Playlist vs Vanilla XMult Jokers")
    print(f"{'=' * 70}")
    print("""
  For Rare rarity, Playlist should compare to:
    - The Idol:     X2 when playing scored face card matching suit (conditional)
    - Obelisk:      X1 base, +X0.2 per consecutive hand of non-most-played type
    - Hologram:     X0.25 per card added to deck

  Playlist (streak-seeking): avg XMult bonus/blind = {:.2f}
  Effective per-hand XMult ≈ {:.2f}x on bonus hands

  Verdict: Playlist is [compare to targets above]
""".format(ev_xmult_s, ev_xmult_s / HANDS_PER_BLIND + 1))


if __name__ == "__main__":
    main()
