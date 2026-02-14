"""
Experiment 0: Vanilla Baseline Scoring Model

Balatro scoring simulator — foundation for all PhoneDeck experiments.
Models the complete scoring pipeline: hand detection, base scoring,
card chip values, joker effects (additive chips/mult, xmult), and
hand leveling.

Usage:
    python experiments/scoring_model.py          # Run validation tests
    from scoring_model import *                  # Import in other experiments
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from enum import IntEnum
from itertools import combinations
from typing import Optional


# ---------------------------------------------------------------------------
# Card model
# ---------------------------------------------------------------------------

class Suit(IntEnum):
    HEARTS = 0
    DIAMONDS = 1
    CLUBS = 2
    SPADES = 3


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


RANK_NAMES = {14: "A", 13: "K", 12: "Q", 11: "J"}
SUIT_SYMBOLS = {Suit.HEARTS: "♥", Suit.DIAMONDS: "♦",
                Suit.CLUBS: "♣", Suit.SPADES: "♠"}


@dataclass(frozen=True, order=True)
class Card:
    rank: Rank
    suit: Suit

    @property
    def chip_value(self) -> int:
        """Balatro chip value: A=11, face=10, number=face value."""
        if self.rank == Rank.ACE:
            return 11
        elif self.rank >= Rank.TEN:
            return 10
        else:
            return int(self.rank)

    @property
    def rank_value(self) -> int:
        """Numeric rank for Calculator: A=14, K=13, ..., 2=2."""
        return int(self.rank)

    @property
    def is_face(self) -> bool:
        return self.rank in (Rank.JACK, Rank.QUEEN, Rank.KING)

    @property
    def is_dark_suit(self) -> bool:
        return self.suit in (Suit.CLUBS, Suit.SPADES)

    def __repr__(self):
        r = RANK_NAMES.get(int(self.rank), str(int(self.rank)))
        return f"{r}{SUIT_SYMBOLS[self.suit]}"


def make_deck() -> list[Card]:
    """Standard 52-card deck."""
    return [Card(r, s) for s in Suit for r in Rank]


def draw_hand(deck: list[Card], n: int = 8) -> list[Card]:
    """Draw n cards from deck (mutates deck)."""
    hand = deck[:n]
    del deck[:n]
    return hand


# ---------------------------------------------------------------------------
# Hand types
# ---------------------------------------------------------------------------

class HandType(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    # These require special cards (not in standard deck, but modeled for completeness)
    FIVE_OF_A_KIND = 9
    FLUSH_HOUSE = 10
    FLUSH_FIVE = 11


HAND_NAMES = {
    HandType.HIGH_CARD: "High Card",
    HandType.PAIR: "Pair",
    HandType.TWO_PAIR: "Two Pair",
    HandType.THREE_OF_A_KIND: "Three of a Kind",
    HandType.STRAIGHT: "Straight",
    HandType.FLUSH: "Flush",
    HandType.FULL_HOUSE: "Full House",
    HandType.FOUR_OF_A_KIND: "Four of a Kind",
    HandType.STRAIGHT_FLUSH: "Straight Flush",
    HandType.FIVE_OF_A_KIND: "Five of a Kind",
    HandType.FLUSH_HOUSE: "Flush House",
    HandType.FLUSH_FIVE: "Flush Five",
}

# Base chips and mult at level 1
HAND_BASE: dict[HandType, tuple[int, int]] = {
    HandType.HIGH_CARD:       (5, 1),
    HandType.PAIR:            (10, 2),
    HandType.TWO_PAIR:        (20, 2),
    HandType.THREE_OF_A_KIND: (30, 3),
    HandType.STRAIGHT:        (30, 4),
    HandType.FLUSH:           (35, 4),
    HandType.FULL_HOUSE:      (40, 4),
    HandType.FOUR_OF_A_KIND:  (60, 7),
    HandType.STRAIGHT_FLUSH:  (100, 8),
    HandType.FIVE_OF_A_KIND:  (120, 12),
    HandType.FLUSH_HOUSE:     (140, 14),
    HandType.FLUSH_FIVE:      (160, 16),
}

# Per-level scaling: (chips_per_level, mult_per_level) added for each level > 1
HAND_LEVEL_SCALING: dict[HandType, tuple[int, int]] = {
    HandType.HIGH_CARD:       (10, 1),
    HandType.PAIR:            (15, 1),
    HandType.TWO_PAIR:        (20, 1),
    HandType.THREE_OF_A_KIND: (20, 2),
    HandType.STRAIGHT:        (30, 3),
    HandType.FLUSH:           (15, 2),
    HandType.FULL_HOUSE:      (25, 2),
    HandType.FOUR_OF_A_KIND:  (30, 3),
    HandType.STRAIGHT_FLUSH:  (40, 4),
    HandType.FIVE_OF_A_KIND:  (35, 3),
    HandType.FLUSH_HOUSE:     (40, 4),
    HandType.FLUSH_FIVE:      (40, 3),
}


def hand_base_score(hand_type: HandType, level: int = 1) -> tuple[int, int]:
    """Return (chips, mult) for a hand type at a given level."""
    base_c, base_m = HAND_BASE[hand_type]
    scale_c, scale_m = HAND_LEVEL_SCALING[hand_type]
    return (base_c + scale_c * (level - 1), base_m + scale_m * (level - 1))


# ---------------------------------------------------------------------------
# Hand detection
# ---------------------------------------------------------------------------

def _is_straight(ranks: list[int]) -> bool:
    """Check if sorted unique ranks form a 5-card straight. Handles A-low."""
    if len(ranks) < 5:
        return False
    unique = sorted(set(ranks))
    if len(unique) < 5:
        return False
    # Normal straight: max - min == 4
    if unique[-1] - unique[0] == 4:
        return True
    # Ace-low straight: A,2,3,4,5 → {14,2,3,4,5}
    if set(unique) == {14, 2, 3, 4, 5}:
        return True
    return False


def detect_hand(cards: list[Card]) -> tuple[HandType, list[Card]]:
    """
    Detect the best poker hand type from played cards.
    Returns (hand_type, scoring_cards) where scoring_cards are the cards
    that contribute to the hand (and therefore contribute chip values).

    Cards should be in play order (left to right) — scoring_cards preserves
    this order for positional effects like Flashlight.
    """
    n = len(cards)
    if n == 0:
        return (HandType.HIGH_CARD, [])

    ranks = [c.rank_value for c in cards]
    suits = [c.suit for c in cards]
    rank_counts = Counter(ranks)
    freq = sorted(rank_counts.values(), reverse=True)

    is_flush = n >= 5 and len(set(suits)) == 1
    is_straight = n >= 5 and _is_straight(ranks)

    # Five of a Kind (needs 5 same rank — requires wild/special cards)
    if n >= 5 and freq[0] >= 5:
        if is_flush:
            target_rank = rank_counts.most_common(1)[0][0]
            scoring = [c for c in cards if c.rank_value == target_rank][:5]
            return (HandType.FLUSH_FIVE, scoring)
        target_rank = rank_counts.most_common(1)[0][0]
        scoring = [c for c in cards if c.rank_value == target_rank][:5]
        return (HandType.FIVE_OF_A_KIND, scoring)

    # Flush House (full house + flush)
    if is_flush and n >= 5 and freq[0] >= 3 and freq[1] >= 2:
        return (HandType.FLUSH_HOUSE, list(cards))

    # Straight Flush
    if is_flush and is_straight:
        return (HandType.STRAIGHT_FLUSH, list(cards))

    # Four of a Kind
    if freq[0] >= 4:
        target_rank = rank_counts.most_common(1)[0][0]
        scoring = [c for c in cards if c.rank_value == target_rank]
        return (HandType.FOUR_OF_A_KIND, scoring[:4])

    # Full House
    if n >= 5 and freq[0] >= 3 and freq[1] >= 2:
        return (HandType.FULL_HOUSE, list(cards))

    # Flush
    if is_flush:
        return (HandType.FLUSH, list(cards))

    # Straight
    if is_straight:
        return (HandType.STRAIGHT, list(cards))

    # Three of a Kind
    if freq[0] >= 3:
        target_rank = rank_counts.most_common(1)[0][0]
        scoring = [c for c in cards if c.rank_value == target_rank]
        return (HandType.THREE_OF_A_KIND, scoring[:3])

    # Two Pair
    if len([v for v in freq if v >= 2]) >= 2:
        pair_ranks = [r for r, cnt in rank_counts.most_common() if cnt >= 2][:2]
        scoring = [c for c in cards if c.rank_value in pair_ranks]
        return (HandType.TWO_PAIR, scoring[:4])

    # Pair
    if freq[0] >= 2:
        target_rank = rank_counts.most_common(1)[0][0]
        scoring = [c for c in cards if c.rank_value == target_rank]
        return (HandType.PAIR, scoring[:2])

    # High Card — only the highest card scores
    best = max(cards, key=lambda c: (c.rank_value, c.chip_value))
    return (HandType.HIGH_CARD, [best])


def best_play(hand: list[Card], play_size: int = 5) -> tuple[HandType, list[Card], list[Card]]:
    """
    From a hand of cards, find the best 5-card (or play_size) combination to play.
    Returns (hand_type, played_cards, scoring_cards).

    Evaluates all C(n, play_size) combinations and picks the highest hand type,
    breaking ties by total chip value of scoring cards. Early-exits on Straight Flush.
    """
    best_ht = HandType.HIGH_CARD
    best_played = None
    best_scoring = None
    best_chip_sum = -1

    for combo in combinations(hand, min(play_size, len(hand))):
        played = list(combo)
        ht, scoring = detect_hand(played)
        chip_sum = sum(c.chip_value for c in scoring)
        if (ht > best_ht) or (ht == best_ht and chip_sum > best_chip_sum):
            best_ht = ht
            best_played = played
            best_scoring = scoring
            best_chip_sum = chip_sum
            # Can't do better than Straight Flush with a standard deck
            if best_ht >= HandType.STRAIGHT_FLUSH:
                break

    if best_played is None:
        # Fallback: play all cards
        ht, scoring = detect_hand(hand)
        return (ht, hand, scoring)

    return (best_ht, best_played, best_scoring)


def best_play_fast(hand: list[Card], play_size: int = 5) -> tuple[HandType, list[Card], list[Card]]:
    """
    Fast heuristic best-play: checks flush/straight first, then rank-based hands.
    ~10x faster than exhaustive best_play() for large hands.
    """
    if len(hand) <= play_size:
        ht, scoring = detect_hand(hand)
        return (ht, hand, scoring)

    # Check for flush (5+ of same suit)
    from collections import Counter as Ctr
    suit_counts = Ctr(c.suit for c in hand)
    flush_suit = None
    for s, cnt in suit_counts.items():
        if cnt >= 5:
            flush_suit = s
            break

    if flush_suit is not None:
        flush_cards = sorted([c for c in hand if c.suit == flush_suit],
                             key=lambda c: c.rank_value, reverse=True)[:5]
        ht, scoring = detect_hand(flush_cards)
        if ht >= HandType.STRAIGHT_FLUSH:
            return (ht, flush_cards, scoring)
        # Keep as candidate
        flush_result = (ht, flush_cards, scoring)
    else:
        flush_result = None

    # Check rank-based hands: sort by frequency then rank
    rank_groups = Ctr(c.rank_value for c in hand)
    # Sort: most frequent first, then highest rank
    sorted_ranks = sorted(rank_groups.keys(),
                          key=lambda r: (rank_groups[r], r), reverse=True)

    # Try to build the best rank-based hand
    selected = []
    for rank in sorted_ranks:
        cards_of_rank = [c for c in hand if c.rank_value == rank]
        selected.extend(cards_of_rank)
        if len(selected) >= play_size:
            break
    selected = selected[:play_size]

    ht_rank, scoring_rank = detect_hand(selected)

    # Also check for straights
    unique_ranks = sorted(set(c.rank_value for c in hand), reverse=True)
    straight_cards = None
    if len(unique_ranks) >= 5:
        for start_idx in range(len(unique_ranks) - 4):
            window = unique_ranks[start_idx:start_idx + 5]
            if window[0] - window[4] == 4:
                straight_cards = []
                for r in window:
                    straight_cards.append(next(c for c in hand if c.rank_value == r))
                break
        # Check A-low straight
        if straight_cards is None and 14 in unique_ranks:
            low = [r for r in unique_ranks if r <= 5]
            if set(low) >= {2, 3, 4, 5}:
                straight_cards = []
                for r in [14, 5, 4, 3, 2]:
                    straight_cards.append(next(c for c in hand if c.rank_value == r))

    if straight_cards:
        ht_str, scoring_str = detect_hand(straight_cards)
    else:
        ht_str = HandType.HIGH_CARD
        scoring_str = []

    # Pick the best among flush, rank-based, and straight
    candidates = [(ht_rank, selected, scoring_rank)]
    if flush_result:
        candidates.append(flush_result)
    if ht_str > HandType.HIGH_CARD:
        candidates.append((ht_str, straight_cards, scoring_str))

    best = max(candidates, key=lambda x: (x[0], sum(c.chip_value for c in x[2])))
    return best


# ---------------------------------------------------------------------------
# Ante / Blind score requirements
# ---------------------------------------------------------------------------

# Score required to beat each blind at each Ante (base stake / White stake)
BLIND_SCORES: dict[str, list[int]] = {
    "Small": [300, 800, 2000, 5000, 11000, 20000, 35000, 70000],
    "Big":   [450, 1200, 3000, 7500, 16500, 30000, 52500, 105000],
    "Boss":  [600, 1600, 4000, 10000, 22000, 40000, 70000, 140000],
}


def blind_score(ante: int, blind_type: str = "Boss") -> int:
    """Score needed to beat a blind. ante is 1-indexed."""
    return BLIND_SCORES[blind_type][ante - 1]


# ---------------------------------------------------------------------------
# Scoring context
# ---------------------------------------------------------------------------

@dataclass
class ScoringContext:
    """All state needed for joker scoring calculations."""
    hand_type: HandType = HandType.HIGH_CARD
    scoring_cards: list = field(default_factory=list)
    played_cards: list = field(default_factory=list)
    hand_levels: dict = field(default_factory=lambda: {ht: 1 for ht in HandType})
    hands_remaining: int = 3       # hands left AFTER this play
    hand_number_in_blind: int = 1  # 1-indexed
    round_number: int = 1          # across entire run
    total_cards_played: int = 0    # lifetime count
    last_hand_type: Optional[HandType] = None  # for Camera
    streak_count: int = 0          # for Playlist
    ante: int = 1


# ---------------------------------------------------------------------------
# Joker base class and implementations
# ---------------------------------------------------------------------------

@dataclass
class ScoringResult:
    """Contribution of a joker to a single hand's score."""
    flat_chips: int = 0
    flat_mult: int = 0
    xmult: float = 1.0
    # Per-card bonuses: maps card index (in scoring_cards) to (bonus_chips, bonus_mult)
    card_chips: dict = field(default_factory=dict)
    card_mult: dict = field(default_factory=dict)
    money: int = 0


class Joker:
    """Base joker. Subclass and override methods."""
    name: str = "Base"
    rarity: int = 1  # 1=Common, 2=Uncommon, 3=Rare, 4=Legendary
    cost: int = 4

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        """Main scoring contribution. Called once per hand."""
        return ScoringResult()

    def on_hand_played(self, ctx: ScoringContext):
        """Update state after a hand is played and scored."""
        pass

    def on_round_end(self, ctx: ScoringContext):
        """Update state at end of round."""
        pass

    def reset(self):
        """Reset all state for a fresh simulation."""
        pass

    def __repr__(self):
        return self.name


# --- Common jokers ---

class Calculator(Joker):
    """Sum scored card ranks. Even → +sum Chips. Odd → +sum//2 Mult."""
    name = "Calculator"
    rarity = 1
    cost = 4

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        rank_sum = sum(c.rank_value for c in ctx.scoring_cards)
        if rank_sum % 2 == 0:
            return ScoringResult(flat_chips=rank_sum)
        else:
            return ScoringResult(flat_mult=rank_sum // 2)


class Flashlight(Joker):
    """First scored card has its chip contribution doubled."""
    name = "Flashlight"
    rarity = 1
    cost = 4

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        if ctx.scoring_cards:
            return ScoringResult(card_chips={0: ctx.scoring_cards[0].chip_value})
        return ScoringResult()


class FitnessTracker(Joker):
    """Gains +1 Chip permanently for every card played this run."""
    name = "Fitness Tracker"
    rarity = 1
    cost = 5

    def __init__(self):
        self._total_cards = 0

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        return ScoringResult(flat_chips=self._total_cards)

    def on_hand_played(self, ctx: ScoringContext):
        self._total_cards += len(ctx.played_cards)

    def reset(self):
        self._total_cards = 0


# --- Uncommon jokers ---

class Camera(Joker):
    """If this hand type matches the last hand played, +25 Mult."""
    name = "Camera"
    rarity = 2
    cost = 6

    def __init__(self):
        self._last_hand = None

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        bonus = 25 if (self._last_hand is not None
                       and ctx.hand_type == self._last_hand) else 0
        return ScoringResult(flat_mult=bonus)

    def on_hand_played(self, ctx: ScoringContext):
        self._last_hand = ctx.hand_type

    def reset(self):
        self._last_hand = None


class Maps(Joker):
    """+20 Mult on Straights/SFs, scaling +5 per Straight/SF played. +$2 per."""
    name = "Maps"
    rarity = 2
    cost = 6

    def __init__(self):
        self._bonus_mult = 0

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        if ctx.hand_type in (HandType.STRAIGHT, HandType.STRAIGHT_FLUSH):
            return ScoringResult(flat_mult=20 + self._bonus_mult, money=2)
        return ScoringResult()

    def on_hand_played(self, ctx: ScoringContext):
        if ctx.hand_type in (HandType.STRAIGHT, HandType.STRAIGHT_FLUSH):
            self._bonus_mult += 5

    def reset(self):
        self._bonus_mult = 0


class DoomScrolling(Joker):
    """Gain +4 Mult per round. Lose 1 discard per round."""
    name = "Doom Scrolling"
    rarity = 2
    cost = 5

    def __init__(self):
        self._rounds = 0

    @property
    def mult_bonus(self) -> int:
        return 4 * self._rounds

    @property
    def discards_lost(self) -> int:
        return self._rounds

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        return ScoringResult(flat_mult=self.mult_bonus)

    def on_round_end(self, ctx: ScoringContext):
        self._rounds += 1

    def reset(self):
        self._rounds = 0


class AlarmClock(Joker):
    """X2 Mult on last hand of round (0 hands remaining after play)."""
    name = "Alarm Clock"
    rarity = 2
    cost = 5

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        if ctx.hands_remaining == 0:
            return ScoringResult(xmult=2.0)
        return ScoringResult()


class Messenger(Joker):
    """Accumulate unread messages. Pair/Two Pair cashes in +3 Mult per unread."""
    name = "Messenger"
    rarity = 2
    cost = 5

    def __init__(self):
        self._unread = 0

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        if ctx.hand_type in (HandType.PAIR, HandType.TWO_PAIR) and self._unread > 0:
            bonus = 3 * self._unread
            return ScoringResult(flat_mult=bonus)
        return ScoringResult()

    def on_hand_played(self, ctx: ScoringContext):
        if ctx.hand_type in (HandType.PAIR, HandType.TWO_PAIR):
            self._unread = 0
        self._unread += 1  # Always accumulate after (so first hand = 1 unread for next)

    def reset(self):
        self._unread = 0


class Timer(Joker):
    """+4 Mult per hand remaining when blind is beaten."""
    name = "Timer"
    rarity = 2
    cost = 6

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        # Timer only gives bonus on the winning hand, but for EV calculation
        # we model it as: if this is the last hand needed (we beat the blind),
        # we get +4 * hands_remaining.  In practice, experiments will handle
        # the conditional scoring.  For per-hand scoring, we approximate by
        # giving the bonus only when hands_remaining > 0 on the last hand.
        return ScoringResult(flat_mult=4 * ctx.hands_remaining)


class DarkMode(Joker):
    """Dark suit cards (Spades/Clubs) +5 Mult. Light suit -2 Mult."""
    name = "Dark Mode"
    rarity = 2
    cost = 6

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        bonus = 0
        for c in ctx.scoring_cards:
            if c.is_dark_suit:
                bonus += 5
            else:
                bonus -= 2
        return ScoringResult(flat_mult=bonus)


# --- Rare jokers ---

class Playlist(Joker):
    """Consecutive same-hand streak: 2nd=X1.5, 3rd=X2.0, 4th+=X2.5."""
    name = "Playlist"
    rarity = 3
    cost = 8

    def __init__(self):
        self._streak = 0
        self._last_hand = None

    STREAK_XMULT = {0: 1.0, 1: 1.5, 2: 2.0}  # 3+ → 2.5

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        # Streak from PREVIOUS hands; current hand extends or resets it
        if self._last_hand is not None and ctx.hand_type == self._last_hand:
            streak = self._streak + 1
        else:
            streak = 0
        xm = self.STREAK_XMULT.get(streak, 2.5)
        return ScoringResult(xmult=xm)

    def on_hand_played(self, ctx: ScoringContext):
        if self._last_hand is not None and ctx.hand_type == self._last_hand:
            self._streak += 1
        else:
            self._streak = 0
        self._last_hand = ctx.hand_type

    def reset(self):
        self._streak = 0
        self._last_hand = None


class Battery(Joker):
    """Starts at X3. Loses X0.25 per hand in a round. Recharges on efficient win."""
    name = "Battery"
    rarity = 3
    cost = 8

    def __init__(self):
        self._charge = 3.0

    @property
    def charge(self) -> float:
        return self._charge

    def calculate(self, ctx: ScoringContext) -> ScoringResult:
        xm = max(self._charge - 0.25 * (ctx.hand_number_in_blind - 1), 0.0)
        return ScoringResult(xmult=xm)

    def recharge(self):
        """Call when blind is beaten with hands remaining."""
        self._charge = 3.0

    def deplete(self):
        """Call when blind is beaten with 0 hands remaining (no recharge)."""
        # Charge carries over but doesn't reset
        pass

    def on_round_end(self, ctx: ScoringContext):
        if ctx.hands_remaining > 0:
            self._charge = 3.0

    def reset(self):
        self._charge = 3.0


class Stocks(Joker):
    """Portfolio: +$1/hand. End of round: 30% triple, 50% hold, 20% crash."""
    name = "Stocks"
    rarity = 3
    cost = 7

    def __init__(self):
        self._portfolio = 0

    @property
    def portfolio(self) -> int:
        return self._portfolio

    def on_hand_played(self, ctx: ScoringContext):
        self._portfolio += 1

    def on_round_end(self, ctx: ScoringContext):
        roll = random.random()
        if roll < 0.30:
            self._portfolio *= 3
        elif roll < 0.80:
            pass  # hold
        else:
            self._portfolio = 0

    def reset(self):
        self._portfolio = 0


# --- Legendary joker ---

class DoNotDisturb(Joker):
    """Boss Blind effects are completely disabled."""
    name = "Do Not Disturb"
    rarity = 4
    cost = 20
    # Effect is modeled in deck/run simulation, not in per-hand scoring.


# ---------------------------------------------------------------------------
# All candidate jokers
# ---------------------------------------------------------------------------

ALL_JOKERS: list[type] = [
    Calculator, Flashlight, FitnessTracker,           # Common (1-3)
    Camera, Maps, DoomScrolling, AlarmClock,           # Uncommon (4-7)
    Messenger, Timer, DarkMode,                        # Uncommon alternates (8-10)
    Playlist, Battery, Stocks,                         # Rare (11-13)
    DoNotDisturb,                                      # Legendary (14)
]

JOKER_BY_NAME: dict[str, type] = {cls.name: cls for cls in ALL_JOKERS}


def make_joker(name: str) -> Joker:
    """Instantiate a joker by name."""
    return JOKER_BY_NAME[name]()


# ---------------------------------------------------------------------------
# Core scoring function
# ---------------------------------------------------------------------------

def score_hand(
    played_cards: list[Card],
    jokers: list[Joker] | None = None,
    hand_levels: dict[HandType, int] | None = None,
    hands_remaining: int = 3,
    hand_number_in_blind: int = 1,
    round_number: int = 1,
    total_cards_played: int = 0,
    last_hand_type: HandType | None = None,
    streak_count: int = 0,
    ante: int = 1,
) -> tuple[int, HandType, list[Card]]:
    """
    Score a played hand through the full Balatro pipeline.

    Returns (final_score, hand_type, scoring_cards).

    Pipeline:
    1. Detect hand type and scoring cards
    2. Base chips + mult from hand type and level
    3. Add each scoring card's chip value
    4. Apply per-card joker bonuses (e.g. Flashlight)
    5. Apply each joker's flat chips, flat mult, xmult
    6. final_score = chips * mult
    """
    if jokers is None:
        jokers = []
    if hand_levels is None:
        hand_levels = {ht: 1 for ht in HandType}

    # Step 1: Detect hand
    hand_type, scoring_cards = detect_hand(played_cards)

    # Step 2: Base score
    level = hand_levels.get(hand_type, 1)
    chips, mult = hand_base_score(hand_type, level)

    # Build context
    ctx = ScoringContext(
        hand_type=hand_type,
        scoring_cards=scoring_cards,
        played_cards=played_cards,
        hand_levels=hand_levels,
        hands_remaining=hands_remaining,
        hand_number_in_blind=hand_number_in_blind,
        round_number=round_number,
        total_cards_played=total_cards_played,
        last_hand_type=last_hand_type,
        streak_count=streak_count,
        ante=ante,
    )

    # Step 3: Add scoring card chip values
    for c in scoring_cards:
        chips += c.chip_value

    # Steps 4-5: Apply joker effects
    for joker in jokers:
        result = joker.calculate(ctx)
        # Per-card bonuses
        for idx, bonus_c in result.card_chips.items():
            if 0 <= idx < len(scoring_cards):
                chips += bonus_c
        for idx, bonus_m in result.card_mult.items():
            if 0 <= idx < len(scoring_cards):
                mult += bonus_m
        # Flat bonuses
        chips += result.flat_chips
        mult += result.flat_mult
        # Multiplicative mult (applied sequentially)
        if result.xmult != 1.0:
            mult = mult * result.xmult

    # Step 6: Final score
    final_score = int(chips * mult)
    return (final_score, hand_type, scoring_cards)


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def simulate_hand(
    deck: list[Card] | None = None,
    hand_size: int = 8,
    play_size: int = 5,
    jokers: list[Joker] | None = None,
    fast: bool = True,
    **kwargs,
) -> tuple[int, HandType]:
    """
    Draw a hand, find the best play, and score it.
    Returns (score, hand_type). Deck is NOT mutated (uses a copy).
    """
    if deck is None:
        deck = make_deck()
    d = list(deck)
    random.shuffle(d)
    hand = d[:hand_size]
    play_fn = best_play_fast if fast else best_play
    _, played, scoring = play_fn(hand, play_size)
    score, ht, _ = score_hand(played, jokers=jokers, **kwargs)
    return (score, ht)


def simulate_hands(
    n: int = 1000,
    jokers: list[Joker] | None = None,
    hand_size: int = 8,
    fast: bool = True,
    **kwargs,
) -> list[tuple[int, HandType]]:
    """Run n random hands and return list of (score, hand_type)."""
    deck = make_deck()
    play_fn = best_play_fast if fast else best_play
    results = []
    for _ in range(n):
        d = list(deck)
        random.shuffle(d)
        hand = d[:hand_size]
        _, played, scoring = play_fn(hand)
        score, ht, _ = score_hand(played, jokers=jokers, **kwargs)
        results.append((score, ht))
    return results


# ---------------------------------------------------------------------------
# Discard simulation
# ---------------------------------------------------------------------------

def best_play_with_discards(
    deck_cards: list[Card],
    hand_size: int = 8,
    play_size: int = 5,
    num_discards: int = 3,
) -> tuple[HandType, list[Card], list[Card]]:
    """
    Simulate drawing a hand and using discards to improve it.
    Uses a greedy heuristic: discard cards not part of the best current hand,
    redraw, and repeat for each discard available.

    Returns (hand_type, played_cards, scoring_cards) for the final play.
    """
    remaining = list(deck_cards)
    random.shuffle(remaining)
    hand = remaining[:hand_size]
    draw_pile = remaining[hand_size:]

    for _ in range(num_discards):
        ht, played, scoring = best_play_fast(hand, play_size)
        if ht >= HandType.FLUSH:
            break  # Good enough, don't discard

        # Identify cards to discard: cards NOT in the best play
        keep = set(id(c) for c in played)
        discard = [c for c in hand if id(c) not in keep]

        if not discard or not draw_pile:
            break

        # Discard worst cards, draw replacements
        n_discard = min(len(discard), len(draw_pile))
        hand = [c for c in hand if id(c) in keep]
        hand.extend(draw_pile[:n_discard])
        draw_pile = draw_pile[n_discard:]

    return best_play_fast(hand, play_size)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def _validate():
    """Run validation tests against known Balatro scoring values."""
    print("=" * 60)
    print("Experiment 0: Vanilla Baseline Scoring Model — Validation")
    print("=" * 60)
    passed = 0
    failed = 0

    def check(desc, actual, expected):
        nonlocal passed, failed
        ok = actual == expected
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {desc}: got {actual}, expected {expected}")
        if ok:
            passed += 1
        else:
            failed += 1

    # --- Hand detection tests ---
    print("\nHand Detection:")

    # Pair
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES),
             Card(Rank.KING, Suit.HEARTS), Card(Rank.QUEEN, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.CLUBS)]
    ht, sc = detect_hand(cards)
    check("Pair of Aces", ht, HandType.PAIR)
    check("Pair scores 2 cards", len(sc), 2)

    # Two Pair
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES),
             Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.CLUBS)]
    ht, sc = detect_hand(cards)
    check("Two Pair", ht, HandType.TWO_PAIR)
    check("Two Pair scores 4 cards", len(sc), 4)

    # Three of a Kind
    cards = [Card(Rank.JACK, Suit.HEARTS), Card(Rank.JACK, Suit.SPADES),
             Card(Rank.JACK, Suit.CLUBS), Card(Rank.QUEEN, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.CLUBS)]
    ht, sc = detect_hand(cards)
    check("Three Jacks", ht, HandType.THREE_OF_A_KIND)
    check("Three of a Kind scores 3 cards", len(sc), 3)

    # Straight (A-high)
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.SPADES),
             Card(Rank.QUEEN, Suit.CLUBS), Card(Rank.JACK, Suit.DIAMONDS),
             Card(Rank.TEN, Suit.HEARTS)]
    ht, sc = detect_hand(cards)
    check("A-high Straight", ht, HandType.STRAIGHT)
    check("Straight scores 5 cards", len(sc), 5)

    # Straight (A-low: A,2,3,4,5)
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.TWO, Suit.SPADES),
             Card(Rank.THREE, Suit.CLUBS), Card(Rank.FOUR, Suit.DIAMONDS),
             Card(Rank.FIVE, Suit.HEARTS)]
    ht, sc = detect_hand(cards)
    check("A-low Straight", ht, HandType.STRAIGHT)

    # Flush
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS),
             Card(Rank.TEN, Suit.HEARTS), Card(Rank.FIVE, Suit.HEARTS),
             Card(Rank.TWO, Suit.HEARTS)]
    ht, sc = detect_hand(cards)
    check("Hearts Flush", ht, HandType.FLUSH)

    # Full House
    cards = [Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.SPADES),
             Card(Rank.KING, Suit.CLUBS), Card(Rank.FIVE, Suit.DIAMONDS),
             Card(Rank.FIVE, Suit.HEARTS)]
    ht, sc = detect_hand(cards)
    check("Full House K-5", ht, HandType.FULL_HOUSE)
    check("Full House scores 5 cards", len(sc), 5)

    # Four of a Kind
    cards = [Card(Rank.SEVEN, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES),
             Card(Rank.SEVEN, Suit.CLUBS), Card(Rank.SEVEN, Suit.DIAMONDS),
             Card(Rank.ACE, Suit.HEARTS)]
    ht, sc = detect_hand(cards)
    check("Four 7s", ht, HandType.FOUR_OF_A_KIND)
    check("Four of a Kind scores 4 cards", len(sc), 4)

    # Straight Flush
    cards = [Card(Rank.NINE, Suit.SPADES), Card(Rank.TEN, Suit.SPADES),
             Card(Rank.JACK, Suit.SPADES), Card(Rank.QUEEN, Suit.SPADES),
             Card(Rank.KING, Suit.SPADES)]
    ht, sc = detect_hand(cards)
    check("Straight Flush 9-K spades", ht, HandType.STRAIGHT_FLUSH)

    # High Card
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.SPADES),
             Card(Rank.TEN, Suit.CLUBS), Card(Rank.FIVE, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.HEARTS)]
    ht, sc = detect_hand(cards)
    check("High Card (no hand)", ht, HandType.HIGH_CARD)
    check("High Card scores 1 card", len(sc), 1)

    # --- Scoring tests ---
    print("\nBase Scoring:")

    # Pair of Aces, level 1: base (10, 2) + 2 aces (11 each) = chips 32, mult 2 → 64
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES),
             Card(Rank.KING, Suit.HEARTS), Card(Rank.QUEEN, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.CLUBS)]
    score, ht, sc = score_hand(cards)
    check("Pair of Aces score", score, (10 + 11 + 11) * 2)  # 32 * 2 = 64

    # Flush (all hearts): A,K,10,5,2 → base (35,4), cards: 11+10+10+5+2=38 → 73*4=292
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS),
             Card(Rank.TEN, Suit.HEARTS), Card(Rank.FIVE, Suit.HEARTS),
             Card(Rank.TWO, Suit.HEARTS)]
    score, ht, sc = score_hand(cards)
    check("Flush A-K-10-5-2 score", score, (35 + 11 + 10 + 10 + 5 + 2) * 4)  # 73*4=292

    # Full House K-5: base (40,4), cards: 10+10+10+5+5=40 → 80*4=320
    cards = [Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.SPADES),
             Card(Rank.KING, Suit.CLUBS), Card(Rank.FIVE, Suit.DIAMONDS),
             Card(Rank.FIVE, Suit.HEARTS)]
    score, ht, sc = score_hand(cards)
    check("Full House K-5 score", score, (40 + 10 + 10 + 10 + 5 + 5) * 4)  # 80*4=320

    # Level 3 Pair: base (10+15*2, 2+1*2) = (40, 4), pair of aces: 40+22=62, 62*4=248
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES),
             Card(Rank.KING, Suit.HEARTS), Card(Rank.QUEEN, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.CLUBS)]
    levels = {ht: 1 for ht in HandType}
    levels[HandType.PAIR] = 3
    score, ht, sc = score_hand(cards, hand_levels=levels)
    check("Level 3 Pair of Aces", score, (40 + 11 + 11) * 4)  # 62*4=248

    # --- Joker tests ---
    print("\nJoker Effects:")

    # Calculator on pair of Aces: rank sum = 14+14 = 28 (even) → +28 chips
    # Base: (10+22)*2 = 64. With Calculator: (10+22+28)*2 = 120
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES),
             Card(Rank.KING, Suit.HEARTS), Card(Rank.QUEEN, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.CLUBS)]
    score, _, _ = score_hand(cards, jokers=[Calculator()])
    check("Calculator even (pair of Aces)", score, (10 + 11 + 11 + 28) * 2)  # 60*2=120

    # Calculator on three 7s: rank sum = 7+7+7 = 21 (odd) → +10 mult
    cards = [Card(Rank.SEVEN, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES),
             Card(Rank.SEVEN, Suit.CLUBS), Card(Rank.QUEEN, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.HEARTS)]
    score, _, _ = score_hand(cards, jokers=[Calculator()])
    check("Calculator odd (three 7s)", score, (30 + 7 + 7 + 7) * (3 + 10))  # 51*13=663

    # Flashlight on flush: first card doubled
    # Flush A,K,10,5,2 hearts: chips = 35+11+10+10+5+2 = 73, flashlight adds 11 → 84*4=336
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS),
             Card(Rank.TEN, Suit.HEARTS), Card(Rank.FIVE, Suit.HEARTS),
             Card(Rank.TWO, Suit.HEARTS)]
    score, _, _ = score_hand(cards, jokers=[Flashlight()])
    # First scoring card is A♥ (chip_value=11), bonus = 11
    check("Flashlight on Flush", score, (35 + 11 + 10 + 10 + 5 + 2 + 11) * 4)  # 84*4=336

    # Alarm Clock: X2 on last hand (hands_remaining=0)
    cards = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES),
             Card(Rank.KING, Suit.HEARTS), Card(Rank.QUEEN, Suit.DIAMONDS),
             Card(Rank.TWO, Suit.CLUBS)]
    score, _, _ = score_hand(cards, jokers=[AlarmClock()], hands_remaining=0)
    check("Alarm Clock last hand", score, int((10 + 11 + 11) * 2 * 2.0))  # 32*4=128

    score, _, _ = score_hand(cards, jokers=[AlarmClock()], hands_remaining=2)
    check("Alarm Clock not last hand", score, (10 + 11 + 11) * 2)  # 64

    # Battery: hand 1 = X3, hand 2 = X2.75
    score1, _, _ = score_hand(cards, jokers=[Battery()], hand_number_in_blind=1)
    check("Battery hand 1 (X3)", score1, int((10 + 11 + 11) * 2 * 3.0))  # 32*6=192

    score2, _, _ = score_hand(cards, jokers=[Battery()], hand_number_in_blind=2)
    check("Battery hand 2 (X2.75)", score2, int((10 + 11 + 11) * 2 * 2.75))  # 32*5.5=176

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    if failed > 0:
        print("\nWARNING: Some tests failed! Check scoring model accuracy.")
    else:
        print("\nAll tests passed. Scoring model validated.")

    return failed == 0


if __name__ == "__main__":
    _validate()
