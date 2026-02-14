# PhoneDeck Mod — Design & Experiment Plan

## Context

We're building a Balatro mod themed around smartphone apps. Each joker represents a phone app whose real-world function maps naturally to a game mechanic. The mod targets "vanilla-plus" quality — it should feel like an official expansion pack, with jokers that are individually interesting AND create emergent synergies with each other and vanilla content.

The existing WeatherDeck mod (1 joker + 1 deck using live weather via `love.https`) serves as our technical reference. PhoneDeck will be a much larger, more ambitious mod: **10 jokers, 1 deck, and optional stretch features**.

This plan has two phases: **(A) candidate design + computational experiments**, then **(B) implementation of the validated winners**. This plan covers Phase A. Engine-level stretch features (notifications, audio, multi-window) are deferred — we can upgrade individual jokers with engine capabilities later.

---

## Candidate Jokers (14 candidates → narrow to 10)

We propose 14 candidates and will use computational experiments to cut to the best 10.

### Common (Rarity 1)

#### 1. Calculator ($4)
**Mechanic:** Sum the ranks of all scored cards (A=14, K=13 ... 2=2). Even sum → add total as Chips. Odd sum → add half (rounded down) as Mult.
**Why it's fun:** Turns every hand into a math puzzle. Do I play for Chips or Mult? Can I swap one card to flip the parity? Simple to understand, deep to optimize.
**Synergy:** Face card builds (high ranks), Flashlight (high first-card chip value), vanilla Scholar/Fibonacci.
**Scoring context:** `context.joker_main`

#### 2. Flashlight ($4)
**Mechanic:** First scored card each hand has its chip contribution doubled (X2 Chips on that card only).
**Why it's fun:** Card positioning matters — put your highest-chip card leftmost. Simple but creates interesting reordering decisions.
**Synergy:** Stone cards (+50 chips doubled = +100), bonus cards, retrigger effects (Red Seal on first card), vanilla Hanging Chad.
**Scoring context:** `context.individual` (triggers on first card in play area)

#### 3. Fitness Tracker ($5)
**Mechanic:** Gains +1 Chip permanently for every card played this entire run. Tooltip shows current count.
**Why it's fun:** Slow-burn snowball. By late game you've played ~200+ cards = +200 Chips. Feels like watching your step count climb. Rewards long runs.
**Synergy:** Benefits from 5-card hands (more cards played), retrigger effects don't help (counts cards played, not scored), vanilla Ice Cream (anti-synergy: IC loses chips).
**Scoring context:** `context.joker_main` (flat chip bonus), state updates on `context.before` or similar

### Uncommon (Rarity 2)

#### 4. Camera ($6)
**Mechanic:** Photographs the poker hand type you just played. If your NEXT hand matches the photo, +25 Mult. Photo updates after every hand regardless.
**Why it's fun:** Rewards planning one hand ahead. "I just played a Flush, can I Flush again?" Creates a rhythm of prediction and execution. The bonus is big enough to warp decisions.
**Synergy:** Playlist (both reward same-hand-type play), Planet cards (leveling one hand), vanilla Supernova (also rewards hand-type awareness).
**Scoring context:** `context.joker_main`

#### 5. Maps ($6)
**Mechanic:** +20 Mult on Straights or Straight Flushes. Each Straight/SF played this run permanently adds +5 Mult to this bonus. Also gain $2 per Straight/SF.
**Why it's fun:** Straights are undervalued in vanilla — this makes them a viable build path. Scaling + economy in one joker. "Charting a new route" each run.
**Synergy:** Shortcut (straights with gaps), Four Fingers, vanilla Fibonacci, Run (if it existed). Anti-synergy with Four of a Kind builds.
**Scoring context:** `context.joker_main`

#### 6. Doom Scrolling ($5)
**Mechanic:** Gain +4 Mult permanently at end of each round. But: lose 1 discard next round (min 0 discards). Current bonus shown on tooltip.
**Why it's fun:** Addictive by design — mirrors real doom scrolling. The mult grows and grows but your discards vanish. By round 6 you have +24 Mult but 0 discards. Tough tradeoff.
**Synergy:** Alarm Clock (fewer discards = more pressure to use last hand), vanilla Merry Andy (anti-synergy: gives discards back), Drunkard.
**Scoring context:** `context.joker_main` (bonus), `context.end_of_round` (scaling + discard loss)

#### 7. Alarm Clock ($5)
**Mechanic:** On your LAST hand of each round (0 hands remaining after playing): X2 Mult.
**Why it's fun:** Creates dramatic "buzzer beater" moments. Do you burn hands early, or carefully save the last one for the big X2? Tension every round.
**Synergy:** Doom Scrolling (synergy cluster — fewer discards means you're likelier to reach your last hand). Battery (ANTI-synergy — Battery wants unused hands). Calculator (big hand on last play). Vanilla: Luchador, Swashbuckler.
**Scoring context:** `context.joker_main` (conditional on remaining hands == 0 after this play)

### Rare (Rarity 3)

#### 8. Playlist ($8)
**Mechanic:** Playing the same poker hand type consecutively builds a streak: 1st play = no bonus, 2nd = X1.5, 3rd = X2.0, 4th+ = X2.5 Mult. Playing a different hand type resets streak to 0.
**Why it's fun:** Massive XMult potential but demands commitment. Do you play suboptimal hands to keep the streak? Creates a "one more song" feeling. High skill ceiling — you need to read your deck.
**Synergy:** Camera (+25 Mult on matches + X2.5 from streak = insane), Planet cards (leveling one hand type), deck thinning. Anti-synergy with Camera's flexibility.
**Scoring context:** `context.joker_main`

#### 9. Battery ($8)
**Mechanic:** Starts at X3 Mult. Loses X0.25 per hand played in a round. Recharges to X3 when you defeat a blind with 1+ hands remaining.
**Why it's fun:** Energy management puzzle. First hand = X3 (incredible), fourth hand = X2.25 (still good), twelfth hand = X0 (dead). Rewards efficient play. Creates genuine tension about "one more hand" vs "save the charge."
**Synergy:** Timer (both reward efficiency), Alarm Clock (DIRECT TENSION — Alarm wants all hands used, Battery wants hands saved). Vanilla: Blueprint (copy the X3 early), Merry Andy (more discards = fewer hands needed).
**Scoring context:** `context.joker_main`

#### 10. Stocks ($7)
**Mechanic:** Portfolio starts at $0. Each hand played deposits $1 into portfolio. At end of round: 30% chance portfolio triples (jackpot!), 50% chance stays same (rolls over), 20% chance portfolio resets to $0 (crash!). Portfolio paid out when you sell the joker OR at end of run.
**Why it's fun:** Investment simulation! The portfolio can reach incredible amounts if you get lucky streaks of non-crashes. Selling at the right time is a metagame decision. "Diamond hands or paper hands?"
**Synergy:** Economy-focused builds, vanilla Egg (also sell-value joker), To the Moon (if portfolio survives). Anti-synergy with selling strategies (you want to hold).
**Scoring context:** `context.end_of_round` (portfolio update), sell value tracks portfolio

### Legendary (Rarity 4)

#### 11. Do Not Disturb ($20)
**Mechanic:** Boss Blind effects are completely disabled.
**Why it's fun:** Thematically perfect — you silenced your phone, no disturbances. Mechanically incredible: no more The Plant debuffing your face cards, no more The Hook discarding your hand. Game-changing legendary.
**Synergy:** Everything — removes the biggest source of disruption. Makes consistent builds more reliable.
**Scoring context:** Hooks into boss blind application, prevents effects

### Alternate Candidates (pick from these if experiments cut any above)

#### 12. Messenger ($5, Uncommon)
**Mechanic:** Each hand played adds 1 "unread message." Playing a Pair or Two Pair "checks messages": gain +3 Mult per unread message, then clear inbox.
**Why it's fun:** Charge-up/release mechanic. Do you keep accumulating messages or cash in? Pairs are common enough to trigger but you want to wait for max value.
**Synergy:** Vanilla Mime (retrigger pairs), The Duo (pair bonus), Jolly Joker.

#### 13. Timer ($6, Uncommon)
**Mechanic:** +4 Mult for each hand remaining when you beat the blind.
**Why it's fun:** Rewards speed/efficiency. Beat a blind in 1 hand with 3 remaining = +12 Mult. Creates the same efficiency puzzle as Battery but as flat Mult.
**Synergy:** Battery (same efficiency cluster), Alarm Clock (ANTI-synergy: Timer wants hands saved, Alarm wants last hand used).

#### 14. Dark Mode ($6, Uncommon)
**Mechanic:** All Spade and Club cards (dark suits) give +5 Mult when scored. Heart and Diamond cards (light suits) give -2 Mult when scored.
**Why it's fun:** Forces suit-aware play. Can you build a deck of only dark-suit cards? Creates interesting draft decisions. "Switching to dark mode."
**Synergy:** Flush builds (dark suits only), Smeared Joker (converts suits), vanilla Arrowhead, Onyx Agate.

---

## Smartphone Deck (b_smartphone)

**Mechanic:**
- Start with 1 random PhoneDeck joker (Eternal — can't be sold)
- +1 hand size (hold 9 cards instead of 8)
- -1 discard (start with 2 instead of 3)
- All joker sell values are +$1 (apps monetize everything)

**Why it's fun:** The random starter joker creates massive replayability — your first joker dictates your build direction. +1 hand size is powerful (more combo potential), -1 discard is a real cost. The sell bonus synergizes with Stocks and economy play.

---

## Engine Stretch Goals (Deferred — Upgrade Later)

These are future upgrades that could make specific jokers more impressive. Each joker will start as pure Lua, and we can add engine backing later:

- **love.notify** — macOS notifications. Upgrade path for a "Push Notification" joker.
- **love.audio extensions** — Custom sounds/pitch shift. Upgrade path for Playlist (streak sounds), Battery (low-power audio cue).
- **love.clipboard** — System clipboard. Upgrade path for a "Copy Paste" joker variant.
- **love.window** — Multi-window. Hardest, but "Picture-in-Picture" mini-game would be incredible.

---

## Computational Experiments

All experiments are Python scripts that model Balatro mechanics. No actual gameplay.

### Experiment 0: Vanilla Baseline Scoring Model
**What:** Build a scoring simulator that models Balatro's hand scoring formula (Chips × Mult), hand base values, card chip values, and joker effects.
**Approach:**
- Implement `score_hand(cards, hand_type, jokers, hand_level)` function
- Model all 10 poker hand types with base chips/mult and per-level scaling
- Card chip values: A=11, K/Q/J=10, 10=10, 9=9, ..., 2=2
- Support additive chips, additive mult, and xmult from jokers
- Validate against known Balatro calculations
**Output:** Scoring function reusable by all other experiments.
**"Good" result:** Matches Balatro wiki examples exactly.

### Experiment 1: Ante Score Requirements Curve
**What:** Model the score needed to beat each blind at each Ante (1-8) and each stake.
**Approach:**
- Blind scores: Small = 300/800/2000/5000/11000/20000/35000/70000, Big = 450/1200/3000/7500/16500/30000/52500/105000, Boss = 600/1600/4000/10000/22000/40000/70000/140000 (base stake)
- Plot the exponential growth curve
- Calculate "what base hand + joker combo beats each blind"
**Output:** Target power levels for each Ante. Our jokers should help reach these thresholds.
**"Good" result:** Clear power curve showing where vanilla jokers of each rarity contribute.

### Experiment 2: Individual Joker Expected Value
**What:** For each of our 14 candidate jokers, compute average score contribution per hand across a simulated run.
**Approach:**
- Generate random 5-card hands from a standard 52-card deck (10,000 samples per Ante)
- Detect poker hand type for each
- Apply each joker's effect and measure delta vs. no-joker baseline
- Track across Antes 1-8 (hand levels increase, base chips/mult grow)
- For scaling jokers (Fitness, Camera, Doom Scrolling), simulate state accumulation over ~30 hands per Ante
**Parameters to sweep:** Hand level (1-5), number of hands per round (1-4), total cards played
**Output:** Power curve per joker per Ante, compared to vanilla jokers of same rarity.
**"Good" result:** Common jokers contribute ~10-30% of score at their Ante, Uncommon ~20-50%, Rare ~40-80%, Legendary = transformative. No joker should be dead weight by Ante 4+.

### Experiment 3: Calculator Parity Analysis
**What:** How often does Calculator give Chips vs Mult? Is one outcome dramatically better?
**Approach:**
- Generate all possible 5-card hands from a 52-card deck
- Sum ranks for each, compute even/odd distribution
- Compare average Chips-mode value vs Mult-mode value
- Analyze how hand type correlates with parity (are Flushes more likely even? Pairs?)
**Output:** Distribution of Calculator outcomes, expected value per path.
**"Good" result:** Roughly 50/50 split, both modes are useful. No dominant strategy.

### Experiment 4: Playlist Streak Probability
**What:** How often can you maintain a Playlist streak of 2, 3, 4+ hands?
**Approach:**
- Simulate a deck of 52 cards, draw 8-card hands (hand size), find best poker hand type
- Model whether subsequent hands can achieve the same type
- Run 10,000 simulated blinds (4 hands each)
- Track streak length distribution for each hand type
**Output:** P(streak=2), P(streak=3), P(streak=4) for each hand type.
**"Good" result:** Pairs streak easily (P≥60% for 2+), Straights almost never streak. Average XMult from Playlist is comparable to rare vanilla xmult jokers.

### Experiment 5: Battery Charge Curve
**What:** Model Battery's average Mult contribution as a function of play style.
**Approach:**
- Simulate blinds with varying hands-to-beat (1, 2, 3, 4 hands)
- Compute average Battery Mult per hand: X3 on first, X2.75 on second, etc.
- Model recharge probability (what % of blinds are beaten with hands remaining?)
- Compare "aggressive" (use all hands) vs "conservative" (win fast) playstyles
**Parameters to sweep:** Hands per blind (1-4), recharge threshold
**Output:** Battery EV curve, optimal play strategy.
**"Good" result:** Battery rewards skill (winning in fewer hands) without being unusable for players who need all 4 hands. Average xmult should be ~X2.0-2.5.

### Experiment 6: Stocks Portfolio Monte Carlo
**What:** Model Stocks joker's long-term portfolio value.
**Approach:**
- 10,000 simulated runs of 8 Antes × ~4 rounds × ~3 hands
- Each hand: +$1 to portfolio
- Each round: 30% triple, 50% hold, 20% crash
- Track portfolio value over time, final payout distribution
**Output:** Histogram of final portfolio values, expected value, probability of $0.
**"Good" result:** EV is meaningfully positive (+$15-30 over a run), but ~30% chance of ending with $0 creates real stakes. Occasional jackpots of $50+ create memorable moments.

### Experiment 7: Synergy Matrix
**What:** Measure pairwise synergy between all PhoneDeck jokers.
**Approach:**
- For each pair (i, j), simulate 10,000 hands with both jokers active
- Compute: `synergy_ratio = score(i+j) / (score(i) + score(j) - score(baseline))`
- Build a 14×14 matrix
- Identify strongest synergy pairs and anti-synergy pairs
**Output:** Heatmap of synergy ratios. Narrative description of key combos.
**"Good" result:** Several synergy pairs with ratio > 1.3 (super-linear combo). No pair with ratio < 0.7 (anti-synergy should be intentional, not accidental). Key intended synergies (Camera+Playlist, Alarm+Doom Scrolling, Battery+Timer) should show up as hot spots.

### Experiment 8: Doom Scrolling Viability Window
**What:** At what round does Doom Scrolling's discard cost outweigh its Mult benefit?
**Approach:**
- Simulate runs with Doom Scrolling: track Mult bonus and discard count at each round
- For each round, compute: "could a typical hand + this Mult beat the blind?" vs "can I even MAKE a good hand with N discards?"
- Model hand quality as a function of discards available (more discards = better hand selection)
**Output:** Viability curve showing Doom Scrolling's net impact per round.
**"Good" result:** Positive net value through Ante 5-6, becomes a liability by Ante 7-8 unless paired with discard-granting jokers. Creates a "sell before it kills you" decision.

### Experiment 9: Smartphone Deck Run Simulation
**What:** Model full runs with the Smartphone Deck vs vanilla decks.
**Approach:**
- Simulate simplified full runs (8 Antes, 3 blinds each)
- Random joker acquisition from shop (weighted by rarity)
- Smartphone: starts with random PhoneDeck joker, +1 hand size, -1 discard, +$1 sell values
- Compare to: Red Deck (+1 discard), Blue Deck (+1 hand), Checkered Deck, etc.
- 5,000 runs per deck type
**Output:** Win rate, average Ante reached, average money, average score.
**"Good" result:** Smartphone Deck win rate within 5% of vanilla top-tier decks (not dominant, not unplayable). The random starter joker creates high variance (fun!).

### Experiment 10: Do Not Disturb Impact Assessment
**What:** How much does disabling boss blinds affect run success?
**Approach:**
- Simulate runs with and without boss blind effects
- Model common boss effects: The Plant (debuffs face cards), The Hook (discards 2 cards), The Flint (halves base chips and mult), The Wall (extra large blind), etc.
- Measure score delta and win rate delta
**Output:** Boss blind severity ranking, DnD value assessment.
**"Good" result:** DnD provides ~15-25% win rate improvement. Justifies Legendary rarity. Some bosses it's irrelevant against (The Wall just has big HP), some it's game-changing (The Flint).

---

## Experiment Execution Order

1. **Exp 0** (Baseline scorer) — foundation for everything
2. **Exp 1** (Ante requirements) — establishes target power levels
3. **Exp 2** (Individual joker EV) — first cut of candidates
4. **Exp 3, 4, 5, 6** (deep dives on interesting mechanics) — run in parallel
5. **Exp 7** (synergy matrix) — validates mod cohesion
6. **Exp 8** (Doom Scrolling viability) — balance check on riskiest design
7. **Exp 9, 10** (deck + legendary) — final pieces

After experiments, we cut from 14 to 10 jokers based on:
- Jokers with boring/flat EV curves get cut
- Jokers that don't synergize with the rest get cut
- If two jokers fill the same niche, keep the more interesting one

## Number Tuning Strategy

Every joker has tunable parameters. Experiments will sweep these to find the sweet spot:

| Joker | Parameters to Tune | Target Feel |
|-------|-------------------|-------------|
| Calculator | Rank values (A=14 or 11?), even/odd split | Both paths feel viable, ~50/50 |
| Flashlight | Multiplier on first card (X2? X2.5? X3?) | Meaningful but not broken |
| Fitness Tracker | Chips per card (+1? +2?), when it becomes relevant | Noticeable by Ante 3, strong by Ante 6 |
| Camera | Mult bonus (+20? +25? +30?) | Worth warping hands for, not free |
| Maps | Base mult (+15/+20/+25), scaling (+3/+5/+7), money ($1/$2/$3) | Makes Straights viable, not mandatory |
| Doom Scrolling | Mult/round (+3/+4/+5), discard loss rate (1/round? 1 every 2?) | Tempting early, scary late |
| Alarm Clock | XMult on last hand (X1.5/X2/X2.5) | Big enough to plan for, not auto-win |
| Playlist | Streak multipliers (X1.3/X1.5/X2.0 vs X1.5/X2.0/X2.5) | Comparable to rare vanilla xmult jokers |
| Battery | Start value (X2.5/X3/X3.5), decay rate (X0.2/X0.25/X0.3) | Avg X2.0-2.5 over a blind |
| Stocks | Deposit rate ($1/$2), triple%/hold%/crash% (30/50/20 vs 25/55/20) | EV +$15-30/run, ~30% total loss chance |
| Do Not Disturb | N/A (binary effect) | Legendary-tier impact |

The experiments will produce recommended values for each parameter, plus sensitivity analysis showing which parameters matter most (and which can be set loosely).

---

## Key Files to Modify/Create (Implementation Phase)

| Path | Purpose |
|------|---------|
| `mods/phonedeck/mod.conf` | Mod manifest |
| `mods/phonedeck/lua/PhoneDeck.lua` | Main mod file (all jokers, deck, hooks) |
| `mods/phonedeck/assets/1x/*.png` | 1x sprites (71x95) |
| `mods/phonedeck/assets/2x/*.png` | 2x sprites (142x190) |
| `experiments/scoring_model.py` | Exp 0: Vanilla scoring simulator |
| `experiments/ante_curve.py` | Exp 1: Ante requirements |
| `experiments/joker_ev.py` | Exp 2: Individual joker EV |
| `experiments/calculator_parity.py` | Exp 3: Calculator analysis |
| `experiments/playlist_streaks.py` | Exp 4: Playlist streak probability |
| `experiments/battery_curve.py` | Exp 5: Battery charge modeling |
| `experiments/stocks_monte_carlo.py` | Exp 6: Stocks portfolio simulation |
| `experiments/synergy_matrix.py` | Exp 7: Pairwise synergy analysis |
| `experiments/doom_scrolling.py` | Exp 8: Doom Scrolling viability |
| `experiments/deck_simulation.py` | Exp 9: Smartphone Deck runs |
| `experiments/dnd_impact.py` | Exp 10: Do Not Disturb assessment |

## Reusable Code from Existing Mod

From `mods/weatherdeck/lua/WeatherDeck.lua`:
- `oh_load_sprite()` (lines 11-44) — sprite loading, reuse directly
- `Card:set_sprites` post-hook (lines 47-67) — required for custom sprites
- Localization pattern via `Game:set_language` hook (lines 127-167)
- Item registration pattern via `Game:init_item_prototypes` hook (lines 169-213)
- Deck effect pattern via `Back:apply_to_run` hook (lines 215-233)
- Scoring pattern via `Card:calculate_joker` hook (lines 235-287)

## Verification Plan

After experiments are run:
1. Review EV curves — no joker should be strictly dominant or strictly useless
2. Synergy matrix should show intentional clusters (efficiency, scaling, economy)
3. Deck simulation should show competitive but not dominant win rate
4. Run sensitivity analysis: small parameter tweaks shouldn't wildly change rankings
5. After Lua implementation: `make build && make install MOD=phonedeck` then launch Balatro and verify all jokers appear in collection, activate correctly, and tooltips render
