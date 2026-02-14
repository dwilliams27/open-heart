"""
Experiment 9: Smartphone Deck Run Simulation

Simulates full 8-Ante runs with the Smartphone Deck vs vanilla decks.
Compares win rates, average scores, and economy.

Usage:
    python experiments/deck_simulation.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring_model import (
    HandType, HAND_NAMES, make_deck, best_play_fast, best_play_with_discards,
    score_hand, BLIND_SCORES, ALL_JOKERS, hand_base_score,
    Card, Rank, Suit, Joker, DoNotDisturb,
)
import random
from collections import defaultdict


N_RUNS = 2000
ANTES = 8
BLINDS_PER_ANTE = 3  # Small, Big, Boss
BASE_HANDS = 4
BASE_DISCARDS = 3
BASE_HAND_SIZE = 8
BASE_MONEY = 4  # Starting money
JOKER_SLOTS = 5

# Simplified shop: chance of finding jokers by rarity
SHOP_RARITY_WEIGHTS = {1: 0.60, 2: 0.25, 3: 0.10, 4: 0.05}

# Hand level progression: buy ~1 planet per 2 antes
LEVEL_SCHEDULE = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5}


class RunState:
    """Simplified Balatro run state."""

    def __init__(self, hand_size=BASE_HAND_SIZE, discards=BASE_DISCARDS,
                 hands=BASE_HANDS, money=BASE_MONEY, jokers=None,
                 sell_bonus=0):
        self.hand_size = hand_size
        self.discards = discards
        self.hands = hands
        self.money = money
        self.jokers: list[Joker] = jokers or []
        self.sell_bonus = sell_bonus
        self.deck = make_deck()
        self.hand_levels = {ht: 1 for ht in HandType}
        self.ante = 1
        self.total_hands_played = 0
        self.total_score = 0
        self.alive = True

    def play_blind(self, blind_type: str) -> bool:
        """Play a single blind. Returns True if beaten."""
        target = BLIND_SCORES[blind_type][self.ante - 1]
        cumulative = 0

        d = list(self.deck)
        random.shuffle(d)
        draw_pile = list(d)

        for h in range(self.hands):
            if len(draw_pile) < self.hand_size:
                draw_pile = list(self.deck)
                random.shuffle(draw_pile)

            hand = draw_pile[:self.hand_size]
            draw_pile = draw_pile[self.hand_size:]

            # Use discards to improve hand
            remaining_discards = self.discards
            best_ht_so_far = HandType.HIGH_CARD
            best_played = hand[:5]

            # Greedy discard strategy
            ht, played, scoring = best_play_with_discards(
                list(d), hand_size=self.hand_size,
                num_discards=min(remaining_discards, 2),  # Use up to 2 discards
            )

            hands_remaining = self.hands - h - 1
            score, _, _ = score_hand(
                played, jokers=self.jokers, hand_levels=self.hand_levels,
                hands_remaining=hands_remaining,
                hand_number_in_blind=h + 1,
                total_cards_played=self.total_hands_played * 5,
                ante=self.ante,
            )

            cumulative += score
            self.total_hands_played += 1
            self.total_score += score

            # Notify jokers
            from scoring_model import ScoringContext, detect_hand
            ht_actual, scoring_actual = detect_hand(played)
            ctx = ScoringContext(
                hand_type=ht_actual,
                scoring_cards=scoring_actual,
                played_cards=played,
                hand_levels=self.hand_levels,
                hands_remaining=hands_remaining,
                hand_number_in_blind=h + 1,
                total_cards_played=self.total_hands_played * 5,
                ante=self.ante,
            )
            for joker in self.jokers:
                joker.on_hand_played(ctx)

            if cumulative >= target:
                # Beat the blind with hands remaining
                ctx.hands_remaining = hands_remaining
                for joker in self.jokers:
                    joker.on_round_end(ctx)
                return True

        # Failed to beat blind
        for joker in self.jokers:
            joker.on_round_end(ScoringContext(ante=self.ante))
        return False

    def shop_phase(self):
        """Simplified shop: maybe buy a joker."""
        # Earn interest: $1 per $5, max $5
        interest = min(self.money // 5, 5)
        self.money += interest + 4  # Base $4 per round

        # Try to buy a joker if we have room and money
        if len(self.jokers) < JOKER_SLOTS and self.money >= 4:
            # Random joker from pool
            roll = random.random()
            cum = 0
            rarity = 1
            for r, w in SHOP_RARITY_WEIGHTS.items():
                cum += w
                if roll < cum:
                    rarity = r
                    break

            # Pick a random joker of this rarity
            available = [cls for cls in ALL_JOKERS
                         if cls.rarity == rarity
                         and cls.name not in {j.name for j in self.jokers}]
            if available and self.money >= available[0].cost:
                cls = random.choice(available)
                if self.money >= cls.cost:
                    joker = cls()
                    self.jokers.append(joker)
                    self.money -= cls.cost

        # Level up a hand type (simplified planet card)
        if random.random() < 0.4:  # ~40% chance per shop visit
            ht = random.choice(list(HandType)[:9])  # Standard hands only
            self.hand_levels[ht] = self.hand_levels.get(ht, 1) + 1

    def run_ante(self) -> bool:
        """Run a full Ante (3 blinds + shops). Returns True if survived."""
        for i, blind_type in enumerate(["Small", "Big", "Boss"]):
            if not self.play_blind(blind_type):
                self.alive = False
                return False
            if i < 2:  # Shop after Small and Big, not after Boss
                self.shop_phase()
        self.ante += 1
        # Level up hands based on schedule
        target_level = LEVEL_SCHEDULE.get(self.ante, 5)
        for ht in HandType:
            if self.hand_levels.get(ht, 1) < target_level:
                self.hand_levels[ht] = target_level
        return True


def simulate_run(deck_type="vanilla", phonedeck_jokers=None):
    """Simulate a full run. Returns (won, ante_reached, total_score, money)."""
    if deck_type == "vanilla":
        state = RunState()
    elif deck_type == "red":
        state = RunState(discards=BASE_DISCARDS + 1)  # +1 discard
    elif deck_type == "blue":
        state = RunState(hands=BASE_HANDS + 1)  # +1 hand
    elif deck_type == "smartphone":
        # Smartphone deck: +1 hand size, -1 discard, +$1 sell values, random starter joker
        starter_cls = random.choice([cls for cls in ALL_JOKERS
                                      if cls.rarity <= 3 and cls is not DoNotDisturb])
        starter = starter_cls()
        state = RunState(
            hand_size=BASE_HAND_SIZE + 1,
            discards=BASE_DISCARDS - 1,
            jokers=[starter],
            sell_bonus=1,
        )
    else:
        state = RunState()

    for ante in range(1, ANTES + 1):
        state.ante = ante
        if not state.run_ante():
            return (False, ante, state.total_score, state.money)

    return (True, ANTES, state.total_score, state.money)


def main():
    random.seed(42)

    print("=" * 70)
    print("Experiment 9: Smartphone Deck Run Simulation")
    print(f"({N_RUNS:,} runs per deck type)")
    print("=" * 70)

    deck_types = ["vanilla", "red", "blue", "smartphone"]

    results = {}
    for dt in deck_types:
        wins = 0
        antes = []
        scores = []
        moneys = []

        for _ in range(N_RUNS):
            won, ante, score, money = simulate_run(dt)
            if won:
                wins += 1
            antes.append(ante)
            scores.append(score)
            moneys.append(money)

        win_rate = wins / N_RUNS * 100
        avg_ante = sum(antes) / len(antes)
        avg_score = sum(scores) / len(scores)
        avg_money = sum(moneys) / len(moneys)
        median_ante = sorted(antes)[len(antes) // 2]

        results[dt] = {
            "win_rate": win_rate,
            "avg_ante": avg_ante,
            "median_ante": median_ante,
            "avg_score": avg_score,
            "avg_money": avg_money,
            "ante_dist": defaultdict(int),
        }
        for a in antes:
            results[dt]["ante_dist"][a] += 1

    # Summary table
    print(f"\n  {'Deck':<12} {'Win Rate':>8} {'Avg Ante':>8} {'Med Ante':>8} "
          f"{'Avg Score':>12} {'Avg Money':>10}")
    print(f"  {'-' * 62}")
    for dt in deck_types:
        r = results[dt]
        print(f"  {dt:<12} {r['win_rate']:>7.1f}% {r['avg_ante']:>8.2f} "
              f"{r['median_ante']:>8} {r['avg_score']:>12,.0f} ${r['avg_money']:>9,.0f}")

    # Ante distribution
    print(f"\n  Ante Reached Distribution (% of runs):")
    print(f"  {'Deck':<12}", end="")
    for a in range(1, ANTES + 1):
        print(f" {'A' + str(a):>6}", end="")
    print()
    print(f"  {'-' * 62}")
    for dt in deck_types:
        dist = results[dt]["ante_dist"]
        print(f"  {dt:<12}", end="")
        for a in range(1, ANTES + 1):
            pct = dist.get(a, 0) / N_RUNS * 100
            print(f" {pct:>5.1f}%", end="")
        print()

    # Smartphone deck detail: starter joker impact
    print(f"\n{'=' * 70}")
    print("Smartphone Deck: Starter Joker Analysis")
    print(f"{'=' * 70}")

    random.seed(42)
    starter_results = defaultdict(lambda: {"wins": 0, "total": 0, "antes": []})

    for _ in range(N_RUNS):
        starter_cls = random.choice([cls for cls in ALL_JOKERS
                                      if cls.rarity <= 3 and cls is not DoNotDisturb])
        starter_name = starter_cls.name

        starter = starter_cls()
        state = RunState(
            hand_size=BASE_HAND_SIZE + 1,
            discards=BASE_DISCARDS - 1,
            jokers=[starter],
            sell_bonus=1,
        )

        won = True
        final_ante = ANTES
        for ante in range(1, ANTES + 1):
            state.ante = ante
            if not state.run_ante():
                won = False
                final_ante = ante
                break

        starter_results[starter_name]["total"] += 1
        if won:
            starter_results[starter_name]["wins"] += 1
        starter_results[starter_name]["antes"].append(final_ante)

    print(f"\n  {'Starter Joker':<20} {'Count':>6} {'Win Rate':>8} {'Avg Ante':>8}")
    print(f"  {'-' * 46}")

    for name in sorted(starter_results.keys(),
                       key=lambda n: starter_results[n]["wins"] / max(starter_results[n]["total"], 1),
                       reverse=True):
        data = starter_results[name]
        if data["total"] < 20:
            continue  # Skip low sample sizes
        wr = data["wins"] / data["total"] * 100
        avg_a = sum(data["antes"]) / len(data["antes"])
        print(f"  {name:<20} {data['total']:>6} {wr:>7.1f}% {avg_a:>8.2f}")

    # Variance analysis
    print(f"\n{'=' * 70}")
    print("Smartphone Deck: Variance Analysis")
    print(f"{'=' * 70}")

    for dt in ["vanilla", "smartphone"]:
        antes_list = []
        for _ in range(N_RUNS):
            won, ante, _, _ = simulate_run(dt)
            antes_list.append(ante)
        avg = sum(antes_list) / len(antes_list)
        variance = sum((a - avg) ** 2 for a in antes_list) / len(antes_list)
        std = variance ** 0.5
        print(f"  {dt:<12}: avg ante {avg:.2f}, std {std:.2f}, "
              f"variance {variance:.2f}")

    print(f"\n{'=' * 70}")
    print("KEY FINDINGS:")
    print(f"{'=' * 70}")
    print("""
  Success criteria:
  - Smartphone Deck win rate within 5% of best vanilla deck
  - High variance (from random starter) = fun replayability
  - No single starter joker dominates (>20% win rate advantage)
  - -1 discard is a real cost (not negligible)
  - +1 hand size is a real benefit (enables better combos)

  Smartphone Deck should feel:
  - Powerful but risky (the starter joker shapes your whole run)
  - Different every time (high variance from random starter)
  - Rewarding for players who adapt to their starter
""")


if __name__ == "__main__":
    main()
