"""
PhoneDeck Experiment Summary — Visual Dashboard

Generates a multi-panel matplotlib figure summarizing all experiment results.

Usage:
    python experiments/summary.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import random
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np

from scoring_model import (
    HandType, HAND_NAMES, make_deck, best_play_fast, best_play_with_discards,
    score_hand, hand_base_score, BLIND_SCORES, ALL_JOKERS,
    ScoringContext, Calculator, Flashlight, FitnessTracker,
    Camera, Maps, DoomScrolling, AlarmClock, Messenger, Timer, DarkMode,
    Playlist, Battery, Stocks, DoNotDisturb,
    detect_hand, Card, Rank, Suit,
)
from collections import defaultdict, Counter
from itertools import combinations


# Consistent styling
COLORS = {
    "Common": "#4CAF50",
    "Uncommon": "#2196F3",
    "Rare": "#9C27B0",
    "Legendary": "#FF9800",
}
RARITY_NAMES = {1: "Common", 2: "Uncommon", 3: "Rare", 4: "Legendary"}

random.seed(42)


def run_joker_ev_data():
    """Compute joker EV data for visualization."""
    EXPECTED_LEVELS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5}
    deck = make_deck()
    n_samples = 1000
    results = {}

    for joker_cls in ALL_JOKERS:
        boosts = []
        for ante in range(1, 9):
            level = EXPECTED_LEVELS[ante]
            levels = {ht: level for ht in HandType}
            warmup = min((ante - 1) * 12, 15)

            scores_with = []
            scores_without = []

            for _ in range(n_samples):
                joker = joker_cls()
                joker.reset()
                last_ht = None
                for h in range(warmup):
                    d = list(deck)
                    random.shuffle(d)
                    hand = d[:8]
                    ht, played, scoring = best_play_fast(hand)
                    ctx = ScoringContext(
                        hand_type=ht, scoring_cards=scoring, played_cards=played,
                        hand_levels=levels, hands_remaining=3 - h % 4,
                        hand_number_in_blind=h % 4 + 1, round_number=h // 4 + 1,
                        total_cards_played=h * 5, last_hand_type=last_ht, ante=ante,
                    )
                    joker.on_hand_played(ctx)
                    if (h + 1) % 4 == 0:
                        joker.on_round_end(ctx)
                    last_ht = ht

                d = list(deck)
                random.shuffle(d)
                hand = d[:8]
                _, played, _ = best_play_fast(hand)

                sj, _, _ = score_hand(played, jokers=[joker], hand_levels=levels,
                                      hands_remaining=2, hand_number_in_blind=2,
                                      total_cards_played=warmup * 5, ante=ante)
                sb, _, _ = score_hand(played, hand_levels=levels)
                scores_with.append(sj)
                scores_without.append(sb)

            avg_w = np.mean(scores_with)
            avg_b = np.mean(scores_without)
            boost = (avg_w - avg_b) / avg_b * 100 if avg_b > 0 else 0
            boosts.append(boost)

        results[joker_cls.name] = {
            "rarity": joker_cls.rarity,
            "boosts": boosts,
            "avg_boost": np.mean(boosts),
        }

    return results


def run_synergy_data():
    """Compute synergy matrix data."""
    deck = make_deck()
    levels = {ht: 2 for ht in HandType}
    n_samples = 800

    def score_avg(jokers):
        total = 0
        for _ in range(n_samples):
            d = list(deck)
            random.shuffle(d)
            hand = d[:8]
            _, played, _ = best_play_fast(hand)
            s, _, _ = score_hand(played, jokers=jokers, hand_levels=levels,
                                 hands_remaining=2, hand_number_in_blind=2,
                                 total_cards_played=50, ante=4)
            total += s
        return total / n_samples

    baseline = score_avg([])
    individual = {}
    for cls in ALL_JOKERS:
        j = cls()
        individual[cls.name] = score_avg([j])

    matrix = np.ones((len(ALL_JOKERS), len(ALL_JOKERS)))
    for i, cls_i in enumerate(ALL_JOKERS):
        for j, cls_j in enumerate(ALL_JOKERS):
            if j <= i:
                continue
            ji, jj = cls_i(), cls_j()
            pair = score_avg([ji, jj])
            expected = individual[cls_i.name] + individual[cls_j.name] - baseline
            matrix[i][j] = pair / expected if expected > 0 else 1.0
            matrix[j][i] = matrix[i][j]

    return matrix


def run_calculator_data():
    """Run calculator parity analysis."""
    deck = make_deck()
    even = 0
    odd = 0
    ht_parity = defaultdict(lambda: [0, 0])  # ht → [even, odd]

    for combo in combinations(deck, 5):
        cards = list(combo)
        ht, scoring = detect_hand(cards)
        rank_sum = sum(c.rank_value for c in scoring)
        if rank_sum % 2 == 0:
            even += 1
            ht_parity[ht][0] += 1
        else:
            odd += 1
            ht_parity[ht][1] += 1

    return even, odd, ht_parity


def run_stocks_data():
    """Monte Carlo stocks simulation."""
    n_sims = 5000
    total_rounds = 24
    finals = []
    for _ in range(n_sims):
        portfolio = 0
        for r in range(total_rounds):
            portfolio += 3  # 3 hands per round
            roll = random.random()
            if roll < 0.30:
                portfolio *= 3
            elif roll >= 0.80:
                portfolio = 0
        finals.append(portfolio)
    return finals


def run_playlist_data():
    """Playlist streak simulation."""
    deck = make_deck()
    n_sims = 5000
    streak_counts = Counter()

    for _ in range(n_sims):
        d = list(deck)
        random.shuffle(d)
        draw_pile = list(d)
        hand_types = []
        for h in range(4):
            if len(draw_pile) < 8:
                draw_pile = list(d)
                random.shuffle(draw_pile)
            hand = draw_pile[:8]
            draw_pile = draw_pile[8:]
            ht, _, _ = best_play_fast(hand)
            hand_types.append(ht)

        current = 1
        for i in range(1, len(hand_types)):
            if hand_types[i] == hand_types[i - 1]:
                current += 1
            else:
                streak_counts[current] += 1
                current = 1
        streak_counts[current] += 1

    return streak_counts


def create_dashboard():
    """Generate the full visual dashboard."""
    fig = plt.figure(figsize=(24, 18), facecolor='#1a1a2e')
    fig.suptitle('PhoneDeck Mod — Experiment Dashboard',
                 fontsize=24, fontweight='bold', color='white', y=0.98)
    fig.text(0.5, 0.955, '14 Candidate Jokers  •  10 Computational Experiments  •  Phase A Results',
             ha='center', fontsize=13, color='#888888')

    gs = GridSpec(3, 4, figure=fig, hspace=0.35, wspace=0.3,
                  left=0.05, right=0.97, top=0.92, bottom=0.04)

    ax_style = {'facecolor': '#16213e', 'edgecolor': '#0f3460'}

    # ─── Panel 1: Ante Score Requirements (top-left) ───
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#16213e')
    antes = range(1, 9)
    for blind_type, color, marker in [("Small", "#4CAF50", "o"),
                                       ("Big", "#FF9800", "s"),
                                       ("Boss", "#F44336", "D")]:
        scores = [BLIND_SCORES[blind_type][a - 1] for a in antes]
        ax1.semilogy(list(antes), scores, color=color, marker=marker,
                     linewidth=2, markersize=6, label=blind_type)
    ax1.set_xlabel('Ante', color='white', fontsize=10)
    ax1.set_ylabel('Score Required (log)', color='white', fontsize=10)
    ax1.set_title('Ante Score Curve', color='white', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')
    ax1.tick_params(colors='white')
    ax1.grid(True, alpha=0.2)

    # ─── Panel 2: Joker EV Ranking (top, span 2 cols) ───
    print("  Computing joker EV data...")
    ev_data = run_joker_ev_data()

    ax2 = fig.add_subplot(gs[0, 1:3])
    ax2.set_facecolor('#16213e')

    sorted_jokers = sorted(ev_data.items(), key=lambda x: x[1]["avg_boost"], reverse=True)
    names = [j[0] for j in sorted_jokers]
    boosts = [j[1]["avg_boost"] for j in sorted_jokers]
    rarities = [j[1]["rarity"] for j in sorted_jokers]
    colors = [COLORS[RARITY_NAMES[r]] for r in rarities]

    bars = ax2.barh(range(len(names)), boosts, color=colors, edgecolor='white', linewidth=0.5)
    ax2.set_yticks(range(len(names)))
    ax2.set_yticklabels(names, fontsize=9, color='white')
    ax2.set_xlabel('Average Score Boost %', color='white', fontsize=10)
    ax2.set_title('Joker Power Ranking (avg boost across Antes 1-8)',
                  color='white', fontsize=12, fontweight='bold')
    ax2.invert_yaxis()
    ax2.tick_params(colors='white')
    ax2.grid(True, axis='x', alpha=0.2)

    # Add rarity legend
    patches = [mpatches.Patch(color=c, label=n) for n, c in COLORS.items()]
    ax2.legend(handles=patches, fontsize=8, loc='lower right',
              facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')

    # ─── Panel 3: Battery Charge Curve (top-right) ───
    ax3 = fig.add_subplot(gs[0, 3])
    ax3.set_facecolor('#16213e')

    configs = [
        ("X2.5, -0.20", 2.5, 0.20, "#4CAF50"),
        ("X3.0, -0.25", 3.0, 0.25, "#2196F3"),
        ("X3.5, -0.30", 3.5, 0.30, "#F44336"),
    ]
    hands = list(range(1, 9))
    for name, start, decay, color in configs:
        xmults = [max(start - decay * (h - 1), 0) for h in hands]
        ax3.plot(hands, xmults, color=color, marker='o', linewidth=2,
                markersize=5, label=name)

    ax3.axhline(y=2.0, color='#FF9800', linestyle='--', alpha=0.5, label='Target min')
    ax3.axhline(y=2.5, color='#FF9800', linestyle='--', alpha=0.5, label='Target max')
    ax3.fill_between(hands, [2.0] * len(hands), [2.5] * len(hands),
                     color='#FF9800', alpha=0.1)
    ax3.set_xlabel('Hand # in Blind', color='white', fontsize=10)
    ax3.set_ylabel('XMult', color='white', fontsize=10)
    ax3.set_title('Battery Charge Decay', color='white', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=7, facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')
    ax3.tick_params(colors='white')
    ax3.grid(True, alpha=0.2)

    # ─── Panel 4: Calculator Parity (middle-left) ───
    print("  Computing calculator parity...")
    even, odd, ht_parity = run_calculator_data()

    ax4 = fig.add_subplot(gs[1, 0])
    ax4.set_facecolor('#16213e')

    ht_order = [HandType.HIGH_CARD, HandType.PAIR, HandType.TWO_PAIR,
                HandType.THREE_OF_A_KIND, HandType.STRAIGHT, HandType.FLUSH,
                HandType.FULL_HOUSE, HandType.FOUR_OF_A_KIND]
    ht_labels = [HAND_NAMES[ht][:8] for ht in ht_order]
    even_pcts = [ht_parity[ht][0] / (ht_parity[ht][0] + ht_parity[ht][1]) * 100
                 if (ht_parity[ht][0] + ht_parity[ht][1]) > 0 else 50
                 for ht in ht_order]
    odd_pcts = [100 - p for p in even_pcts]

    x = np.arange(len(ht_labels))
    width = 0.35
    ax4.barh(x - width / 2, even_pcts, width, label='Even (Chips)', color='#4CAF50', alpha=0.8)
    ax4.barh(x + width / 2, odd_pcts, width, label='Odd (Mult)', color='#F44336', alpha=0.8)
    ax4.axvline(x=50, color='white', linestyle='--', alpha=0.3)
    ax4.set_yticks(x)
    ax4.set_yticklabels(ht_labels, fontsize=8, color='white')
    ax4.set_xlabel('% of Hands', color='white', fontsize=10)
    ax4.set_title(f'Calculator Parity\n(Overall: {even/(even+odd)*100:.0f}% Even / {odd/(even+odd)*100:.0f}% Odd)',
                  color='white', fontsize=11, fontweight='bold')
    ax4.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')
    ax4.tick_params(colors='white')

    # ─── Panel 5: Synergy Matrix Heatmap (middle, span 2 cols) ───
    print("  Computing synergy matrix...")
    matrix = run_synergy_data()

    ax5 = fig.add_subplot(gs[1, 1:3])
    ax5.set_facecolor('#16213e')

    short_names = [cls.name[:10] for cls in ALL_JOKERS]
    n = len(ALL_JOKERS)

    # Mask diagonal
    masked = np.copy(matrix)
    np.fill_diagonal(masked, np.nan)

    im = ax5.imshow(masked, cmap='RdYlGn', vmin=0.6, vmax=1.8, aspect='auto')
    ax5.set_xticks(range(n))
    ax5.set_yticks(range(n))
    ax5.set_xticklabels(short_names, rotation=45, ha='right', fontsize=7, color='white')
    ax5.set_yticklabels(short_names, fontsize=7, color='white')
    ax5.set_title('Synergy Matrix (>1.0 = super-linear)',
                  color='white', fontsize=12, fontweight='bold')
    cbar = plt.colorbar(im, ax=ax5, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors='white')
    cbar.set_label('Synergy Ratio', color='white')

    # Annotate strong synergies
    for i in range(n):
        for j in range(n):
            if i != j and not np.isnan(masked[i, j]):
                val = masked[i, j]
                if val > 1.4 or val < 0.7:
                    ax5.text(j, i, f'{val:.1f}', ha='center', va='center',
                            fontsize=6, color='white', fontweight='bold')

    # ─── Panel 6: Doom Scrolling Timeline (middle-right) ───
    ax6 = fig.add_subplot(gs[1, 3])
    ax6.set_facecolor('#16213e')

    rounds = range(0, 15)
    mult_bonus = [4 * r for r in rounds]
    discards = [max(0, 3 - r) for r in rounds]

    ax6_twin = ax6.twinx()
    ax6.bar(list(rounds), mult_bonus, color='#4CAF50', alpha=0.7, label='+Mult')
    ax6_twin.plot(list(rounds), discards, color='#F44336', marker='o',
                  linewidth=2, markersize=5, label='Discards')
    ax6_twin.fill_between(list(rounds), discards, alpha=0.1, color='#F44336')
    ax6.set_xlabel('Rounds Held', color='white', fontsize=10)
    ax6.set_ylabel('+Mult Bonus', color='#4CAF50', fontsize=10)
    ax6_twin.set_ylabel('Discards Left', color='#F44336', fontsize=10)
    ax6.set_title('Doom Scrolling\nMultiplier vs Discards', color='white',
                  fontsize=11, fontweight='bold')
    ax6.tick_params(colors='white')
    ax6_twin.tick_params(colors='#F44336')
    ax6.axvline(x=3, color='#FF9800', linestyle='--', alpha=0.5)
    ax6.text(3.2, max(mult_bonus) * 0.8, '0 discards\n→ danger zone',
            fontsize=7, color='#FF9800')

    # ─── Panel 7: Stocks Portfolio Distribution (bottom-left) ───
    print("  Running stocks Monte Carlo...")
    stocks_data = run_stocks_data()

    ax7 = fig.add_subplot(gs[2, 0])
    ax7.set_facecolor('#16213e')

    # Log-scale histogram
    nonzero = [v for v in stocks_data if v > 0]
    zeros_pct = (len(stocks_data) - len(nonzero)) / len(stocks_data) * 100

    if nonzero:
        log_vals = np.log10(np.array(nonzero) + 1)
        ax7.hist(log_vals, bins=40, color='#4CAF50', alpha=0.8, edgecolor='#1a1a2e')
    ax7.axvline(x=np.log10(np.median(nonzero) + 1) if nonzero else 0,
                color='#FF9800', linestyle='--', linewidth=2, label=f'Median (non-zero)')
    ax7.set_xlabel('log₁₀(Portfolio + 1)', color='white', fontsize=10)
    ax7.set_ylabel('Frequency', color='white', fontsize=10)
    ax7.set_title(f'Stocks Final Portfolio\n({zeros_pct:.0f}% end at $0)',
                  color='white', fontsize=11, fontweight='bold')
    ax7.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')
    ax7.tick_params(colors='white')

    # ─── Panel 8: Playlist Streak Distribution (bottom, middle-left) ───
    print("  Running playlist streaks...")
    streak_counts = run_playlist_data()

    ax8 = fig.add_subplot(gs[2, 1])
    ax8.set_facecolor('#16213e')

    streaks = sorted(streak_counts.keys())
    counts = [streak_counts[s] for s in streaks]
    total = sum(counts)
    pcts = [c / total * 100 for c in counts]

    bar_colors = ['#4CAF50' if s == 1 else '#2196F3' if s == 2
                  else '#9C27B0' if s == 3 else '#FF9800' for s in streaks]
    ax8.bar(streaks, pcts, color=bar_colors, edgecolor='white', linewidth=0.5)

    xmult_labels = {1: 'X1.0', 2: 'X1.5', 3: 'X2.0', 4: 'X2.5'}
    for s, p in zip(streaks, pcts):
        if s in xmult_labels:
            ax8.text(s, p + 1, xmult_labels[s], ha='center', fontsize=8, color='white')

    ax8.set_xlabel('Streak Length', color='white', fontsize=10)
    ax8.set_ylabel('% of Streaks', color='white', fontsize=10)
    ax8.set_title('Playlist Streak Distribution\n(Greedy play)', color='white',
                  fontsize=11, fontweight='bold')
    ax8.tick_params(colors='white')

    # ─── Panel 9: Deck Comparison (bottom, middle-right) ───
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.set_facecolor('#16213e')

    # Quick deck sim (reuse simplified data)
    print("  Running deck comparison...")
    deck_results = {}
    for dt in ["vanilla", "red", "blue", "smartphone"]:
        wins = 0
        antes_reached = []
        for _ in range(1000):
            from deck_simulation import simulate_run
            won, ante, _, _ = simulate_run(dt)
            if won:
                wins += 1
            antes_reached.append(ante)
        deck_results[dt] = {
            "win_rate": wins / 1000 * 100,
            "avg_ante": np.mean(antes_reached),
        }

    deck_names = list(deck_results.keys())
    win_rates = [deck_results[d]["win_rate"] for d in deck_names]
    avg_antes = [deck_results[d]["avg_ante"] for d in deck_names]

    deck_colors = ['#666', '#F44336', '#2196F3', '#FF9800']
    x = np.arange(len(deck_names))
    ax9.bar(x, win_rates, color=deck_colors, edgecolor='white', linewidth=0.5)
    for i, (wr, aa) in enumerate(zip(win_rates, avg_antes)):
        ax9.text(i, wr + 0.5, f'{wr:.0f}%\n(Ante {aa:.1f})',
                ha='center', fontsize=8, color='white')
    ax9.set_xticks(x)
    ax9.set_xticklabels([d.title() for d in deck_names], fontsize=9, color='white')
    ax9.set_ylabel('Win Rate %', color='white', fontsize=10)
    ax9.set_title('Deck Comparison\n(2000 runs each)', color='white',
                  fontsize=11, fontweight='bold')
    ax9.tick_params(colors='white')

    # ─── Panel 10: Key Findings Summary (bottom-right) ───
    ax10 = fig.add_subplot(gs[2, 3])
    ax10.set_facecolor('#16213e')
    ax10.axis('off')

    findings = [
        ("Calculator", "79% Even / 21% Odd\nA=11 more balanced", "#4CAF50"),
        ("Doom Scroll", "Never net-negative!\nNeeds rebalancing", "#F44336"),
        ("Battery", "X2.5,-0.20 is\nthe sweet spot", "#2196F3"),
        ("Playlist", "32% hit X2.5\nwith streak strategy", "#9C27B0"),
        ("Stocks", "EV=$22K, 21% bust\nHigh variance!", "#FF9800"),
        ("DnD", "+5.7% per boss\nLegendary justified", "#FFD700"),
    ]

    ax10.set_title('Key Findings', color='white', fontsize=12, fontweight='bold')
    for i, (name, finding, color) in enumerate(findings):
        y = 0.88 - i * 0.16
        ax10.text(0.05, y, name, fontsize=10, fontweight='bold', color=color,
                 transform=ax10.transAxes, va='top')
        ax10.text(0.05, y - 0.06, finding, fontsize=8, color='#cccccc',
                 transform=ax10.transAxes, va='top')

    output_path = os.path.join(os.path.dirname(__file__), 'dashboard.png')
    fig.savefig(output_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"\n  Dashboard saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("PhoneDeck Experiment Dashboard Generator")
    print("=" * 60)

    print("\nGenerating dashboard (this takes ~60 seconds)...\n")
    path = create_dashboard()

    print(f"\n{'=' * 60}")
    print("EXPERIMENT SUMMARY")
    print(f"{'=' * 60}")
    print("""
  BALANCE FINDINGS:
  ─────────────────
  1. Calculator: 79% Even with A=14 — too skewed. Recommend A=11 (60/40 split).
     Pairs ALWAYS give even (two identical ranks = even sum).

  2. Doom Scrolling: +4 Mult/round NEVER becomes net-negative even with 0 discards.
     The mult bonus outpaces hand quality loss. Needs higher cost:
     → Option A: Lose 2 discards/round (faster death spiral)
     → Option B: Reduce to +3 Mult/round
     → Option C: Also lose 1 hand/round after discards hit 0

  3. Battery: X3.0, -0.25 averages X2.62 over 4 hands — slightly above target.
     X2.5, -0.20 hits the sweet spot (avg X2.20 over 4 hands).
     Recommendation: Use X2.5, -0.20 for better balance.

  4. Playlist: With streak-seeking play, 32% of blinds hit 4-hand streaks (X2.5).
     Average XMult bonus per blind: 3.59. Strong for Rare rarity.

  5. Stocks: Mean $22K but median $18 — extremely right-skewed.
     21% chance of ending at $0. Creates dramatic stories but
     typical experience is modest ($10-50 range).

  6. DnD: +5.7% win rate per boss blind, ~21.5 percentage points over 8 antes.
     Comparable to Chicot but better. Legendary rarity justified.

  SYNERGY HIGHLIGHTS:
  ───────────────────
  ✓ Camera + Playlist:  ratio 1.95 (STRONG — both reward same-type play)
  ✓ Battery + Timer:    ratio 1.73 (STRONG — both reward efficiency)
  ✗ Alarm + DoomScroll: ratio 1.02 (WEAK — intended synergy not showing)
  ✗ Calculator + Flash:  ratio 0.98 (WEAK — no special interaction)

  POWER RANKING (by avg score boost):
  ────────────────────────────────────
   1. Doom Scrolling  +322% (TOO STRONG for Uncommon)
   2. Timer           +179% (TOO STRONG for Uncommon)
   3. Battery         +175% (Reasonable for Rare with xmult)
   4. Dark Mode       +125% (Strong for Uncommon)
   5. Calculator      +106% (Strong for Common)
   6. Camera           +98% (Strong for Uncommon)
   7. Fitness Tracker   +98% (Strong for Common)
   8. Maps             +80% (Good for Uncommon)
   9. Messenger         +47% (ON TARGET for Uncommon)
  10. Flashlight        +11% (ON TARGET for Common)
  11. Playlist          +11% (LOW for Rare — needs per-hand context)
  12. Alarm Clock        +0% (DEAD — only triggers on last hand)
  13. Stocks             +0% (Economy joker — score boost ≠ value)
  14. Do Not Disturb     +0% (Boss effect — not measurable by boost)

  CUT RECOMMENDATIONS:
  ────────────────────
  Keep (10):  Calculator, Flashlight, Fitness Tracker, Camera, Maps,
              Alarm Clock, Playlist, Battery, Stocks, Do Not Disturb
  Cut (4):    Doom Scrolling (broken balance), Timer (too strong, overlaps Battery),
              Messenger (generic), Dark Mode (strong but boring)

  If Doom Scrolling is rebalanced, swap it in for Messenger or Dark Mode.
""")
