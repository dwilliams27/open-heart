# PhoneDeck Mod — Revised Design (Implementation-Ready)

## Overview

PhoneDeck is a Balatro mod themed around smartphone apps: **10 jokers + 1 deck**. Each joker represents a phone app whose real-world function maps to a game mechanic. The mod targets "vanilla-plus" quality — it should feel like an official expansion pack.

**Process:** 14 candidates were designed, tested across 11 computational experiments (Python simulations modeling Balatro scoring, ante curves, synergies, and run outcomes), and narrowed to the best 10. This document is the authoritative blueprint for Phase B implementation.

The original design and experiment plan is preserved in `docs/phonedeck-plan.md`. Experiment scripts are in `experiments/`.

---

## Experiment Results Summary

| Joker | Avg Boost % | Rarity | Verdict |
|---|---|---|---|
| Doom Scrolling | +322% | Uncommon | **CUT** — broken, never net-negative even at 0 discards |
| Timer | +179% | Uncommon | **CUT** — too strong, overlaps Battery's efficiency niche |
| Battery | +175% | Rare | **KEEP** — tune to X2.5 start, -0.20 decay |
| Dark Mode | +125% | Uncommon | **CUT** — strong but generic/boring mechanic |
| Calculator | +106% | Common | **KEEP** — change A=14 to A=11 (79→60% even split) |
| Camera | +98% | Uncommon | **KEEP** |
| Fitness Tracker | +98% | Common | **KEEP** |
| Maps | +80% | Uncommon | **KEEP** |
| Messenger | +47% | Uncommon | **CUT** — generic charge/release, least thematic |
| Flashlight | +11% | Common | **KEEP** — on target for Common |
| Playlist | +11% | Rare | **KEEP** — raw % misleading; XMult context matters |
| Alarm Clock | +0% | Uncommon | **KEEP** — only triggers on last hand, niche by design |
| Stocks | +0% | Rare | **KEEP** — economy joker, score boost ≠ value |
| Do Not Disturb | +0% | Legendary | **KEEP** — +5.7% win rate per boss, Legendary justified |

### Key Experiment Findings

- **Calculator:** With A=14, parity is 79% even / 21% odd — too skewed. Pairs *always* give even (two identical ranks = even sum). Switching to A=11 yields ~60/40 split. Players can choose either parity ~94% of the time from 8-card hands, creating meaningful decisions.
- **Battery:** X3.0/-0.25 averages X2.62 over 4 hands — slightly above target. X2.5/-0.20 hits the sweet spot (avg X2.20 over 4 hands). Goes dead at hand 13 (irrelevant in practice).
- **Playlist:** With streak-seeking play, 32% of blinds hit 4-hand streaks (X2.5). Average XMult bonus per blind: 3.59. Strong for Rare.
- **Stocks:** Mean portfolio $22K but median $18 — extremely right-skewed. 21% chance of ending at $0. High variance creates dramatic stories.
- **DnD:** +5.7% win rate per boss blind, ~21.5 percentage points across 8 antes. Comparable to Chicot but better.
- **Doom Scrolling:** +4 Mult/round never becomes net-negative — the mult bonus always outpaces hand quality loss from losing discards. Fundamentally broken as designed.
- **Synergy highlights:** Camera+Playlist ratio 1.95 (strong), Battery+Timer 1.73 (strong, but Timer is cut). Alarm+DoomScroll 1.02 (intended synergy didn't materialize — moot since both are cut/kept independently).

---

## Final 10 Jokers — Full Specifications

### Common (Rarity 1)

#### 1. Calculator ($4)

**Mechanic:** Sum the ranks of all scored cards (A=11, K=13, Q=12, J=11, number cards = face value). Even sum → add total as Chips. Odd sum → add half (rounded down) as Mult.

**Tooltip text:**
```
"Sum ranks of scored cards",
"({C:attention}A=11{}, K=13, Q=12, J=11)",
"Even: {C:chips}+sum{} Chips",
"Odd: {C:mult}+sum/2{} Mult",
```

**Scoring context:** `context.joker_main`

**State fields:** None (stateless).

**Return values:**
```lua
-- Even:
{ chip_mod = rank_sum, message = localize({type="variable", key="a_chips", vars={rank_sum}}),
  colour = G.C.CHIPS, card = self }
-- Odd:
{ mult_mod = math.floor(rank_sum / 2),
  message = localize({type="variable", key="a_mult", vars={math.floor(rank_sum / 2)}}),
  colour = G.C.MULT, card = self }
```

**Lua notes:** Compute rank sum from `context.scoring_hand`. Use chip_value for Ace (11), rank_value for face cards (J=11, Q=12, K=13), face value for number cards. In Balatro's card model: `card:get_id()` returns rank (2-14, where 14=Ace). For the A=11 tweak: `local val = (id == 14) and 11 or id`.

**Synergies:** Face card builds (high ranks), Flashlight (high first-card chip), vanilla Scholar/Fibonacci.

---

#### 2. Flashlight ($4)

**Mechanic:** First scored card each hand has its chip contribution doubled (effectively +chips equal to that card's chip value).

**Tooltip text:**
```
"First scored card",
"gets {C:chips}X2{} Chips",
```

**Scoring context:** `context.individual` — triggers when `context.cardarea == G.play`.

**State fields:** None. Check card index in `context.scoring_hand` to determine if this is the first card.

**Return values:**
```lua
-- In context.individual, for the first card only:
{ chips = card_chip_value, card = self }
```

**Lua notes:** `context.individual` fires per-card. Check if `context.other_card` is the first entry in the scoring hand. Balatro sorts scoring cards left-to-right; compare against `context.scoring_hand[1]`. Return `{ chips = N }` to add chips for that specific card.

**Synergies:** Stone cards (+50 chips doubled = +100), bonus cards, retrigger effects (Red Seal on first card), vanilla Hanging Chad.

---

#### 3. Fitness Tracker ($5)

**Mechanic:** Gains +1 Chip permanently for every card played this entire run. Tooltip shows current count.

**Tooltip text:**
```
"{C:chips}+1{} Chip for every",
"card played this run",
"{C:green}(Currently {C:chips}+#1#{C:green} Chips){}"
```
Where `#1#` is `card.ability.extra.chips`.

**Scoring context:** `context.joker_main`

**State fields:**
```lua
card.ability.extra = { chips = 0 }
```

**Return values:**
```lua
{ chip_mod = card.ability.extra.chips,
  message = localize({type="variable", key="a_chips", vars={card.ability.extra.chips}}),
  colour = G.C.CHIPS, card = self }
```

**Lua notes:** Increment `card.ability.extra.chips` by the number of cards in `context.full_hand` (the played cards) at the appropriate hook point. Use `context.before` (fires before scoring) to update the count for each hand. Alternatively, update in `context.joker_main` before returning, adding `#context.scoring_hand` or `#context.full_hand`.

Dynamic tooltip: hook `Card:generate_UIBox_ability_table` to update `#1#` with current chip count.

**Synergies:** Benefits from 5-card hands, long runs. Anti-synergy with vanilla Ice Cream (also chip-based but decays).

---

### Uncommon (Rarity 2)

#### 4. Camera ($6)

**Mechanic:** Photographs the poker hand type you just played. If your NEXT hand matches the photo, +25 Mult. Photo updates after every hand regardless.

**Tooltip text:**
```
"{C:mult}+25{} Mult if played hand",
"matches previous hand type",
"{C:green}(Photo: {C:attention}#1#{C:green}){}"
```
Where `#1#` is the last hand type name (or "None" if first hand).

**Scoring context:** `context.joker_main`

**State fields:**
```lua
card.ability.extra = { last_hand = nil }  -- stores hand type string
```

**Return values:**
```lua
-- When hand matches photo:
{ mult_mod = 25, message = localize({type="variable", key="a_mult", vars={25}}),
  colour = G.C.MULT, card = self }
```

**Lua notes:** After scoring (in `context.after` or end of `context.joker_main`), update `card.ability.extra.last_hand` to the current hand type. Compare using `G.GAME.last_hand_played` or track internally. Use `context.before` or check at scoring time.

Dynamic tooltip: show photographed hand type name.

**Synergies:** Playlist (both reward same-type play — confirmed 1.95x synergy ratio), Planet cards, vanilla Supernova.

---

#### 5. Maps ($6)

**Mechanic:** +20 Mult on Straights or Straight Flushes. Each Straight/SF played this run permanently adds +5 Mult to this bonus. Also gain $2 per Straight/SF played.

**Tooltip text:**
```
"{C:mult}+#1#{} Mult if hand is a",
"{C:attention}Straight{} or {C:attention}Straight Flush{}",
"Bonus increases by {C:mult}+5{} each time",
"Also earn {C:money}$2{}"
```
Where `#1#` is `20 + card.ability.extra.bonus`.

**Scoring context:** `context.joker_main`

**State fields:**
```lua
card.ability.extra = { bonus = 0 }  -- accumulated +5 increments
```

**Return values:**
```lua
-- On Straight/SF:
{ mult_mod = 20 + card.ability.extra.bonus,
  message = localize({type="variable", key="a_mult", vars={20 + card.ability.extra.bonus}}),
  colour = G.C.MULT, card = self, dollars = 2 }
```

**Lua notes:** Check `context.scoring_name` or use the hand type detection to match Straight/SF. Update `card.ability.extra.bonus` after scoring. The `dollars` field in the return table grants money.

Dynamic tooltip: show current total mult bonus.

**Synergies:** Shortcut (straights with gaps), Four Fingers, vanilla Fibonacci. Anti-synergy with Four of a Kind builds.

---

#### 6. Alarm Clock ($5)

**Mechanic:** On your LAST hand of each round (0 hands remaining after playing): X2 Mult.

**Tooltip text:**
```
"{X:mult,C:white}X2{} Mult on",
"{C:attention}last hand{} of round"
```

**Scoring context:** `context.joker_main`

**State fields:** None (stateless).

**Return values:**
```lua
-- When hands_remaining == 0:
{ Xmult_mod = 2, message = localize({type="variable", key="a_xmult", vars={2}}),
  colour = G.C.MULT, card = self }
```

**Lua notes:** Check `G.GAME.current_round.hands_left == 0` (after decrementing for current hand). This fires on the final hand. Straightforward conditional.

**Synergies:** Battery (intentional TENSION — Battery wants hands saved, Alarm wants last hand used). Creates "save for X2 vs protect Battery charge" decisions. Calculator (big hand on last play).

---

### Rare (Rarity 3)

#### 7. Playlist ($8)

**Mechanic:** Playing the same poker hand type consecutively builds a streak. 1st play = no bonus (X1.0), 2nd consecutive = X1.5, 3rd = X2.0, 4th+ = X2.5 Mult. Different hand type resets streak.

**Tooltip text:**
```
"Playing same hand type",
"consecutively builds streak:",
"{X:mult,C:white}X1.5{}/{X:mult,C:white}X2{}/{X:mult,C:white}X2.5{} Mult",
"{C:green}(Streak: {C:attention}#1#{C:green}){}"
```
Where `#1#` is current streak count.

**Scoring context:** `context.joker_main`

**State fields:**
```lua
card.ability.extra = { streak = 0, last_hand = nil }
```

**Return values:**
```lua
local STREAK_XMULT = { [0] = 1.0, [1] = 1.5, [2] = 2.0 }  -- 3+ = 2.5
local xm = STREAK_XMULT[streak] or 2.5
-- Only return if xm > 1:
{ Xmult_mod = xm, message = localize({type="variable", key="a_xmult", vars={xm}}),
  colour = G.C.MULT, card = self }
```

**Lua notes:** At scoring time, compute the *prospective* streak (does current hand match last_hand?). After scoring, update state. The streak represents consecutive matches: 0 = first play or mismatch (X1.0), 1 = second consecutive (X1.5), etc. Only return XMult when streak >= 1 (otherwise it's just X1.0 = no visual feedback needed).

Dynamic tooltip: show current streak count and next XMult threshold.

**Synergies:** Camera (confirmed 1.95x synergy — both reward same-type play, stack multiplicatively). Planet cards (leveling one hand type). Deck thinning (more consistent hands).

---

#### 8. Battery ($8)

**Mechanic:** Starts at X2.5 Mult. Loses X0.20 per hand played in a blind. Recharges to X2.5 when you defeat a blind with 1+ hands remaining.

**Tooltip text:**
```
"{X:mult,C:white}X#1#{} Mult",
"Loses {X:mult,C:white}X0.2{} per hand",
"Recharges on efficient win",
```
Where `#1#` is current charge (formatted to 1 decimal).

**Scoring context:** `context.joker_main`

**State fields:**
```lua
card.ability.extra = { current_mult = 2.5 }
```

**Return values:**
```lua
local xm = math.max(card.ability.extra.current_mult - 0.20 * (hand_number - 1), 0)
{ Xmult_mod = xm, message = localize({type="variable", key="a_xmult", vars={xm}}),
  colour = G.C.MULT, card = self }
```

**Lua notes:**
- Hand number tracking: use a local counter that resets each blind, or compute from `G.GAME.current_round.hands_played` (number of hands played this round, 0-indexed).
- XMult per hand: Hand 1 = X2.5, Hand 2 = X2.3, Hand 3 = X2.1, Hand 4 = X1.9. Average over 4 hands = X2.2 (in target range).
- Recharge: in `context.end_of_round` (or equivalent), check `G.GAME.current_round.hands_left > 0`. If so, reset `current_mult` to 2.5. If not, the current charge carries over (it's already depleted from usage).
- The charge *does not* go below 0 — use `math.max`.
- Goes dead at hand 13 (irrelevant in practice, max hands per blind is ~5-6).

Dynamic tooltip: show current charge level.

**Synergies:** Alarm Clock (intentional tension — Battery wants hands saved, Alarm wants last hand used). Vanilla Blueprint (copy the X2.5 early), Merry Andy (more discards = fewer hands needed).

---

#### 9. Stocks ($7)

**Mechanic:** Portfolio starts at $0. Each hand played deposits $1 into portfolio. At end of round: 30% chance portfolio triples, 50% chance holds, 20% chance crashes to $0. Joker sell value equals $7 base + portfolio value.

**Tooltip text:**
```
"Earn {C:money}$1{} per hand to portfolio",
"End of round: {C:green}30%{} triple,",
"{C:attention}50%{} hold, {C:red}20%{} crash",
"{C:money}(Portfolio: $#1#){}"
```
Where `#1#` is current portfolio value.

**Scoring context:** Economy only — no `context.joker_main` scoring return.

**State fields:**
```lua
card.ability.extra = { portfolio = 0 }
```

**Lua notes:**
- Increment portfolio in `context.before` or on hand played.
- End-of-round portfolio event: use `context.end_of_round` with `context.game_over == false`. Roll `pseudorandom('stocks')` or `math.random()` for the 30/50/20 split.
- **Sell value:** Override `card.sell_cost` dynamically. In Balatro, `card.sell_cost` determines what you get when selling. Update it in `Card:generate_UIBox_ability_table` or via a periodic update. Set `card.sell_cost = math.max(1, math.floor((7 + card.ability.extra.portfolio) / 2))` (Balatro sell value = cost/2, so to get portfolio as sell payout, set sell_cost = base + portfolio, but check the vanilla formula).
- Show portfolio event message with `card_eval_status_text` for triple/hold/crash feedback.

Dynamic tooltip: show current portfolio value.

**Synergies:** Economy-focused builds, vanilla Egg (also sell-value joker), Smartphone Deck sell bonus.

---

### Legendary (Rarity 4)

#### 10. Do Not Disturb ($20)

**Mechanic:** Boss Blind effects are completely disabled. The boss still has its increased score requirement, but its special ability (debuffing cards, forcing discards, etc.) is nullified.

**Tooltip text:**
```
"{C:attention}Boss Blind{} effects",
"are completely {C:red}disabled{}"
```

**Scoring context:** Not a scoring joker. Hooks into blind effect application.

**State fields:** None (stateless).

**Lua notes:**
- Hook into `Blind:debuff_card` or `Blind:set_blind` to prevent boss effects.
- In Balatro, boss effects are applied via the Blind class. The cleanest approach: hook `Blind:debuff_hand` / `Blind:debuff_card` and check if any joker in `G.jokers.cards` has key `j_dnd`. If so, return without applying debuffs.
- Alternative: hook `Blind:set_blind` to strip the boss's ability flags before they activate.
- This is similar to how vanilla Chicot works (disables specific boss effects). Study Chicot's implementation for the exact hook points.
- Experiment finding: +5.7% win rate per boss blind, ~21.5 percentage points across a full run. Some bosses it's irrelevant against (The Wall just has big HP), some it's game-changing (The Flint halves chips/mult, The Plant debuffs all face cards).

**Synergies:** Everything — removes the biggest source of disruption. Makes consistent builds more reliable.

---

## Smartphone Deck (b_smartphone)

**Mechanic:**
- Start with 1 random eternal PhoneDeck joker (can't be sold/destroyed)
- +1 hand size (hold 9 cards instead of 8)
- -1 discard (start with 2 instead of 3)
- All joker sell values are +$1

**Tooltip text:**
```
"Start run with a random",
"{C:attention}PhoneDeck{} joker ({C:attention}Eternal{})",
"{C:blue}+1{} hand size, {C:red}-1{} discard",
"{C:money}+$1{} joker sell values"
```

**Implementation:** `Back:apply_to_run` hook (same pattern as WeatherDeck).

```lua
if self.effect.center.key == "b_smartphone" then
    -- +1 hand size
    G.GAME.round_resets.hands = G.GAME.round_resets.hands + 0  -- hand_size handled separately
    G.hand:change_size(1)
    -- -1 discard
    G.GAME.round_resets.discards = G.GAME.round_resets.discards - 1
    -- Random PhoneDeck joker (eternal)
    local pool = {"j_calculator","j_flashlight","j_fitness","j_camera","j_maps",
                   "j_alarm","j_playlist","j_battery","j_stocks","j_dnd"}
    local key = pseudorandom_element(pool, pseudoseed("smartphone"))
    G.E_MANAGER:add_event(Event({
        func = function()
            local card = add_joker(key, nil, nil, true)
            card.ability.eternal = true
            return true
        end,
    }))
end
```

The +$1 sell value bonus: hook `Card:set_cost` or modify `card.sell_cost` for all jokers when this deck is active. Check `G.GAME.selected_back.effect.center.key == "b_smartphone"`.

**Experiment finding:** Smartphone Deck win rate within ~3% of vanilla top-tier decks. The random starter creates high variance (fun!) — getting Battery vs Flashlight as your starter creates very different runs.

---

## Lua Implementation Reference

### Patterns to Copy from WeatherDeck

Source: `mods/weatherdeck/lua/WeatherDeck.lua`

| Pattern | Lines | Action |
|---|---|---|
| `oh_load_sprite()` | 11-44 | Copy verbatim |
| `Card:set_sprites` post-hook | 54-67 | Copy verbatim (fixes vanilla atlas bug) |
| `parse_loc_entry()` helper | 128-137 | Copy verbatim |
| `Game:set_language` hook | 143-167 | Add 10 joker + 1 deck loc entries |
| `Game:init_item_prototypes` hook | 173-213 | Register all 11 centers + load sprites |
| `Back:apply_to_run` hook | 219-233 | Smartphone deck effect |
| `Card:calculate_joker` hook | 239-287 | Main scoring dispatch |

### Return Value Cheat Sheet

```lua
-- Flat chips (context.joker_main):
{ chip_mod = N, message = localize({type="variable", key="a_chips", vars={N}}),
  colour = G.C.CHIPS, card = self }

-- Flat mult (context.joker_main):
{ mult_mod = N, message = localize({type="variable", key="a_mult", vars={N}}),
  colour = G.C.MULT, card = self }

-- XMult (context.joker_main):
{ Xmult_mod = N, message = localize({type="variable", key="a_xmult", vars={N}}),
  colour = G.C.MULT, card = self }

-- Per-card chips (context.individual):
{ chips = N, card = self }

-- Per-card mult (context.individual):
{ mult = N, card = self }

-- Money (add to any return):
{ ..., dollars = N }
```

### Hook Dispatch Structure

The `Card:calculate_joker` hook is one big function that dispatches on `self.config.center.key`:

```lua
local original_calc = Card.calculate_joker
function Card:calculate_joker(context)
    if self.ability.set == "Joker" then
        local key = self.config.center.key

        -- Per-card hooks (context.individual)
        if context.individual and context.cardarea == G.play then
            if key == "j_flashlight" then ... end
        end

        -- Pre-scoring hooks (context.before)
        if context.before then
            if key == "j_fitness" then
                -- update card count
            end
        end

        -- Main scoring hooks (context.joker_main)
        if context.joker_main then
            if key == "j_calculator" then ... end
            if key == "j_camera" then ... end
            if key == "j_maps" then ... end
            if key == "j_alarm" then ... end
            if key == "j_playlist" then ... end
            if key == "j_battery" then ... end
            if key == "j_fitness" then ... end
        end

        -- After-hand hooks (context.after)
        if context.after then
            -- Update Camera photo, Playlist streak, etc.
        end

        -- End of round hooks
        if context.end_of_round and not context.game_over then
            if key == "j_stocks" then ... end
        end
    end

    return original_calc(self, context)
end
```

### Dynamic Tooltip Hook

For stateful jokers (6 of 10 need this), hook `Card:generate_UIBox_ability_table`:

```lua
local original_gen_ui = Card.generate_UIBox_ability_table
function Card:generate_UIBox_ability_table()
    local key = self.config.center.key
    if key == "j_fitness" then
        -- Update #1# with current chip count
    elseif key == "j_camera" then
        -- Update #1# with photographed hand name
    elseif key == "j_battery" then
        -- Update #1# with current charge
    elseif key == "j_playlist" then
        -- Update #1# with current streak
    elseif key == "j_stocks" then
        -- Update #1# with portfolio value
    elseif key == "j_maps" then
        -- Update #1# with current bonus
    end
    return original_gen_ui(self)
end
```

---

## Synergy Clusters

Three intentional synergy clusters, confirmed by experiment:

### 1. Consistency Cluster: Camera + Playlist
- **Ratio:** 1.95x (strongest synergy in the mod)
- **Why:** Both reward playing the same hand type repeatedly. Camera gives +25 flat Mult on matches, Playlist gives up to X2.5 on streaks. These stack multiplicatively: (+25 Mult) × (X2.5) = massive score. Incentivizes extreme commitment to one hand type + deck thinning + Planet cards.

### 2. Efficiency Tension: Battery + Alarm Clock
- **Design:** Intentional tension, not synergy. Battery wants hands saved (recharge on efficient win, higher XMult on early hands). Alarm Clock wants the last hand used (X2 only at 0 hands remaining). The player must choose which to optimize for, or find the sweet spot (use exactly all hands, getting Alarm X2 on the final one while Battery still has ~X1.9).
- This creates interesting decision-making every round.

### 3. Economy Cluster: Stocks + Smartphone Deck
- **Design:** Smartphone Deck's +$1 joker sell values directly buffs Stocks' sell-for-portfolio strategy. The random starter joker from Smartphone Deck might *be* Stocks, starting the portfolio early.
- Vanilla Egg also synergizes (gains sell value over time).

### Additional Notable Interactions
- **Calculator + Flashlight:** Ratio 0.98 (no special interaction, but no anti-synergy either — they operate on different axes).
- **Fitness Tracker + any long-run strategy:** Fitness grows faster in builds that play many cards per hand (5-card plays vs 2-card plays).
- **Maps + Shortcut/Four Fingers:** Vanilla jokers that make Straights easier directly buff Maps' triggers.

---

## Asset Requirements

11 total assets: 10 joker sprites + 1 deck back.

### Asset Keys

| Key | Type | Joker |
|---|---|---|
| `j_calculator` | Joker | Calculator |
| `j_flashlight` | Joker | Flashlight |
| `j_fitness` | Joker | Fitness Tracker |
| `j_camera` | Joker | Camera |
| `j_maps` | Joker | Maps |
| `j_alarm` | Joker | Alarm Clock |
| `j_playlist` | Joker | Playlist |
| `j_battery` | Joker | Battery |
| `j_stocks` | Joker | Stocks |
| `j_dnd` | Joker | Do Not Disturb |
| `b_smartphone` | Back | Smartphone Deck |

### Generation Commands

```bash
make generate MOD=phonedeck ASSET=j_calculator PROMPT="balatro style joker of a mischievous math professor joker hunched over an oversized retro calculator. The calculator screen glows with swirling numbers that float off into the air, some even and golden, some odd and crimson. Scattered playing cards with visible rank numbers orbit around the calculator like electrons. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_flashlight PROMPT="balatro style joker of a detective joker holding a giant glowing flashlight that casts a dramatic cone of brilliant golden light. The beam illuminates a single playing card floating in darkness, making it sparkle and shine while the surrounding cards remain in shadow. Rays of light scatter like a spotlight on a stage. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_fitness PROMPT="balatro style joker of an enthusiastic fitness trainer joker wearing a sweatband and running shoes, flexing while looking at a glowing smartwatch on their wrist. The watch face shows a climbing step counter with little chip icons instead of steps. Small playing cards jog in a line behind the joker like a marathon. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_camera PROMPT="balatro style joker of a photographer joker peering through a vintage polaroid camera with one eye. A just-taken polaroid photo floats in front showing a ghostly image of a poker hand. The camera flash is going off with dramatic starburst light rays. Film strips with tiny card symbols curl around the edges. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_maps PROMPT="balatro style joker of an explorer joker holding a glowing treasure map that unfolds and trails behind them. The map shows winding paths connecting playing card suits like landmarks, with a dotted line forming a straight path through all of them. A compass rose spins in the corner with card suit directions. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_alarm PROMPT="balatro style joker of a frantic joker slamming down on a giant old-fashioned alarm clock that is ringing violently with visible shockwaves. The clock hands point to midnight, bells on top are shaking wildly. Lightning bolts and exclamation sparks fly outward from the impact. The whole scene feels urgent and electric. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_playlist PROMPT="balatro style joker of a DJ joker wearing oversized headphones, spinning a vinyl record on a turntable. Musical notes flow from the headphones in a repeating pattern, each note shaped like a different card suit. The vinyl record has concentric rings that glow in rainbow colors, and a streak counter rises like an equalizer behind them. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_battery PROMPT="balatro style joker of an energetic joker hugging a massive glowing battery that crackles with electricity. The battery shows charge level bars that fade from bright green at the top to dim red at the bottom. Electric arcs jump between the battery terminals and nearby playing cards, charging them up. The whole scene buzzes with contained power. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_stocks PROMPT="balatro style joker of a wall street trader joker in a pinstripe suit, watching a dramatic stock chart that zigzags wildly upward with occasional crashes. Dollar signs and gold coins float around the peaks, while the valleys show scattered broken coins. A ticker tape made of tiny playing cards streams across the background. The joker grips the chart with diamond hands. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_dnd PROMPT="balatro style joker of a zen monk joker sitting in perfect meditation with eyes closed, surrounded by a glowing purple bubble of silence. Outside the bubble, chaotic boss monsters and disruptions rage and claw at the shield but cannot break through. A crescent moon symbol floats above the joker's head. Inside the bubble everything is peaceful and still. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=b_smartphone PROMPT="balatro style playing card back design featuring a sleek smartphone screen as the centerpiece. The phone screen shows a grid of colorful app icons, each icon shaped like a different card suit or joker symbol. The phone frame is ornate and jeweled like a luxury case. Radiating signal waves emanate from the phone in concentric circles. Dark rich background with circuit board patterns. NO TEXT AT ALL"
```

---

## File Structure

```
mods/phonedeck/
├── mod.conf               # MOD_ENGINE_DEPS="" (pure Lua)
├── lua/
│   └── PhoneDeck.lua      # All jokers, deck, hooks
└── assets/
    ├── 1x/                # 71x95 per sprite
    │   ├── j_calculator.png
    │   ├── j_flashlight.png
    │   ├── j_fitness.png
    │   ├── j_camera.png
    │   ├── j_maps.png
    │   ├── j_alarm.png
    │   ├── j_playlist.png
    │   ├── j_battery.png
    │   ├── j_stocks.png
    │   ├── j_dnd.png
    │   └── b_smartphone.png
    └── 2x/                # 142x190 per sprite
        ├── j_calculator.png
        ├── j_flashlight.png
        ├── j_fitness.png
        ├── j_camera.png
        ├── j_maps.png
        ├── j_alarm.png
        ├── j_playlist.png
        ├── j_battery.png
        ├── j_stocks.png
        ├── j_dnd.png
        └── b_smartphone.png
```

---

## Engine Stretch Goals (Deferred)

Same as original plan. PhoneDeck is a pure Lua mod — no engine dependencies. Future upgrades that could enhance specific jokers:

- **love.notify** — macOS notifications. Upgrade path for a "Push Notification" joker.
- **love.audio extensions** — Custom sounds/pitch shift. Upgrade path for Playlist (streak sounds), Battery (low-power audio cue).
- **love.clipboard** — System clipboard. Upgrade path for a "Copy Paste" joker variant.
- **love.window** — Multi-window. "Picture-in-Picture" mini-game would be incredible but hardest to implement.

---

## Verification Plan

1. `make build` (no engine deps needed — pure Lua mod, but need LÖVE binary)
2. `make install MOD=phonedeck`
3. Launch Balatro, verify all 10 jokers appear in the collection
4. Verify Smartphone Deck appears in deck selection
5. Test each joker's scoring effect in a run:
   - Calculator: play even/odd hands, verify correct chips/mult
   - Flashlight: verify first card gets doubled chips
   - Fitness Tracker: verify chip count increases across hands
   - Camera: play same hand twice, verify +25 Mult on second
   - Maps: play Straights, verify scaling +5 Mult
   - Alarm Clock: use last hand, verify X2
   - Playlist: maintain streak, verify X1.5→X2.0→X2.5 progression
   - Battery: play multiple hands, verify decaying XMult
   - Stocks: play rounds, observe triple/hold/crash events
   - DnD: encounter boss blind, verify effects are disabled
6. Test dynamic tooltips update correctly for all 6 stateful jokers
7. Test Stocks sell value reflects portfolio
8. Test Smartphone Deck grants random eternal joker + hand size + discard changes
