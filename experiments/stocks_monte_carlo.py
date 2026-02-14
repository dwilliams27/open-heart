"""
Experiment 6: Stocks Portfolio Monte Carlo

Simulates the Stocks joker's portfolio mechanics over full runs.
Answers: what's the EV, probability of $0, jackpot distribution?

Usage:
    python experiments/stocks_monte_carlo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import random
from collections import defaultdict
import math


# Run structure
ANTES = 8
ROUNDS_PER_ANTE = 3  # Small, Big, Boss
HANDS_PER_ROUND = 3  # Average hands used per round
N_SIMULATIONS = 10000


def simulate_portfolio(
    deposit_per_hand=1,
    triple_pct=0.30,
    hold_pct=0.50,
    crash_pct=0.20,
    n_sims=N_SIMULATIONS,
):
    """
    Simulate Stocks portfolio over a full run.
    Returns list of final portfolio values.
    """
    total_rounds = ANTES * ROUNDS_PER_ANTE
    total_hands = total_rounds * HANDS_PER_ROUND

    final_values = []
    peak_values = []
    crash_counts = []
    triple_counts = []
    history_sum = defaultdict(float)  # round_number → avg portfolio

    for _ in range(n_sims):
        portfolio = 0
        peak = 0
        crashes = 0
        triples = 0

        for r in range(total_rounds):
            # Play hands, depositing money
            for h in range(HANDS_PER_ROUND):
                portfolio += deposit_per_hand

            # End of round: roll
            roll = random.random()
            if roll < triple_pct:
                portfolio *= 3
                triples += 1
            elif roll < triple_pct + hold_pct:
                pass  # hold
            else:
                portfolio = 0
                crashes += 1

            peak = max(peak, portfolio)
            history_sum[r] += portfolio

        final_values.append(portfolio)
        peak_values.append(peak)
        crash_counts.append(crashes)
        triple_counts.append(triples)

    return final_values, peak_values, crash_counts, triple_counts, history_sum


def print_histogram(values, label, buckets=20):
    """Simple text histogram."""
    if not values:
        return
    mn, mx = min(values), max(values)
    if mn == mx:
        print(f"    All values = {mn}")
        return

    # Use log scale for wide ranges
    step = max(1, (mx - mn) // buckets)
    bins = defaultdict(int)
    for v in values:
        b = (v // step) * step
        bins[b] += 1

    max_count = max(bins.values())
    sorted_bins = sorted(bins.items())[:buckets]

    for b, count in sorted_bins:
        bar_len = int(count / max_count * 40) if max_count > 0 else 0
        bar = "█" * bar_len
        pct = count / len(values) * 100
        print(f"    ${b:>6} - ${b + step - 1:<6}: {bar} ({pct:.1f}%)")

    # Show tail if truncated
    if len(sorted_bins) < len(bins):
        remaining = sum(c for b, c in bins.items() if b > sorted_bins[-1][0])
        pct = remaining / len(values) * 100
        print(f"    ${sorted_bins[-1][0] + step:>6}+       : ... ({pct:.1f}%)")


def analyze_config(name, deposit, triple, hold, crash, n_sims=N_SIMULATIONS):
    """Run and analyze a single configuration."""
    print(f"\n  --- {name} ---")
    print(f"  Deposit: ${deposit}/hand, Triple: {triple*100:.0f}%, "
          f"Hold: {hold*100:.0f}%, Crash: {crash*100:.0f}%")

    finals, peaks, crashes, triples, history = simulate_portfolio(
        deposit, triple, hold, crash, n_sims
    )

    # Statistics
    zeros = sum(1 for v in finals if v == 0)
    nonzeros = [v for v in finals if v > 0]
    avg = sum(finals) / len(finals)
    median = sorted(finals)[len(finals) // 2]
    p90 = sorted(finals)[int(len(finals) * 0.9)]
    p99 = sorted(finals)[int(len(finals) * 0.99)]
    mx = max(finals)
    avg_peak = sum(peaks) / len(peaks)
    avg_crashes = sum(crashes) / len(crashes)
    avg_triples = sum(triples) / len(triples)

    print(f"\n  Final Portfolio Statistics ({n_sims:,} runs):")
    print(f"    Mean:              ${avg:,.0f}")
    print(f"    Median:            ${median:,}")
    print(f"    P90:               ${p90:,}")
    print(f"    P99:               ${p99:,}")
    print(f"    Max:               ${mx:,}")
    print(f"    Ended at $0:       {zeros/len(finals)*100:.1f}% ({zeros:,} runs)")
    if nonzeros:
        avg_nonzero = sum(nonzeros) / len(nonzeros)
        print(f"    Avg (if non-zero): ${avg_nonzero:,.0f}")
    print(f"    Avg peak reached:  ${avg_peak:,.0f}")
    print(f"    Avg crashes/run:   {avg_crashes:.1f}")
    print(f"    Avg triples/run:   {avg_triples:.1f}")

    # Distribution of final values
    print(f"\n  Final Value Distribution:")
    print_histogram(finals, "Final $")

    # Portfolio growth over time
    total_rounds = ANTES * ROUNDS_PER_ANTE
    print(f"\n  Portfolio Growth Over Time (avg):")
    milestones = [0, 3, 6, 9, 12, 15, 18, 21, 23]
    for r in milestones:
        if r < total_rounds:
            avg_at_r = history[r] / n_sims
            ante = r // ROUNDS_PER_ANTE + 1
            blind = ["Small", "Big", "Boss"][r % ROUNDS_PER_ANTE]
            print(f"    Round {r+1:>2} (Ante {ante} {blind:<5}): ${avg_at_r:>8.0f}")

    return avg, zeros / len(finals) * 100, median


def main():
    random.seed(42)

    print("=" * 70)
    print("Experiment 6: Stocks Portfolio Monte Carlo")
    print(f"({N_SIMULATIONS:,} simulated runs)")
    print("=" * 70)

    # Configuration sweep
    configs = [
        ("Design (30/50/20)", 1, 0.30, 0.50, 0.20),
        ("Low Risk (25/60/15)", 1, 0.25, 0.60, 0.15),
        ("High Risk (35/40/25)", 1, 0.35, 0.40, 0.25),
        ("Double Deposit (30/50/20)", 2, 0.30, 0.50, 0.20),
        ("Lucky (40/45/15)", 1, 0.40, 0.45, 0.15),
    ]

    summary = []
    for name, deposit, triple, hold, crash in configs:
        avg, zero_pct, median = analyze_config(name, deposit, triple, hold, crash)
        summary.append((name, avg, zero_pct, median))

    # Summary comparison
    print(f"\n{'=' * 70}")
    print("SUMMARY COMPARISON")
    print(f"{'=' * 70}")
    print(f"\n  {'Config':<30} {'EV':>8} {'Median':>8} {'$0 Rate':>8}")
    print(f"  {'-' * 56}")
    for name, avg, zero_pct, median in summary:
        print(f"  {name:<30} ${avg:>6.0f} ${median:>6} {zero_pct:>7.1f}%")

    # Sell timing analysis
    print(f"\n{'=' * 70}")
    print("SELL TIMING ANALYSIS: When Should You Sell Stocks?")
    print(f"{'=' * 70}")

    random.seed(42)
    total_rounds = ANTES * ROUNDS_PER_ANTE

    # For the design config, track "sell at round R" EV
    print(f"\n  If you sell Stocks at different Antes:")
    print(f"  {'Sell After':>12}  {'EV':>8}  {'$0 Rate':>8}  {'Advice':>15}")
    print(f"  {'-' * 50}")

    for sell_ante in range(1, 9):
        sell_round = sell_ante * ROUNDS_PER_ANTE
        values = []
        for _ in range(10000):
            portfolio = 0
            for r in range(sell_round):
                for h in range(HANDS_PER_ROUND):
                    portfolio += 1
                roll = random.random()
                if roll < 0.30:
                    portfolio *= 3
                elif roll >= 0.80:
                    portfolio = 0
            values.append(portfolio)

        avg = sum(values) / len(values)
        zero_pct = sum(1 for v in values if v == 0) / len(values) * 100
        # Is it worth holding longer?
        advice = "keep" if sell_ante < 6 else "consider selling"
        print(f"  {'Ante ' + str(sell_ante):>12}  ${avg:>6.0f}  {zero_pct:>7.1f}%  {advice:>15}")

    print(f"\n{'=' * 70}")
    print("KEY FINDINGS:")
    print(f"{'=' * 70}")
    print("""
  Questions answered:
  1. Is EV meaningfully positive? Target: +$15-30 per run
  2. Is ~30% chance of $0 achieved? (creates real stakes)
  3. Are occasional jackpots ($50+) possible? (memorable moments)
  4. What's the optimal sell timing?
  5. Which probability config feels best?

  Stocks should feel like:
  - "I COULD sell now for guaranteed $X..."
  - "But if I hold one more round and get a triple..."
  - Occasional massive payoffs that create stories
  - Real pain when a crash wipes a big portfolio
""")


if __name__ == "__main__":
    main()
