-- PhoneDeck — Open Heart gameplay mod
-- Smartphone-themed jokers and deck for Balatro.
-- Phase B: implementing jokers incrementally.

-- ============================================================
-- Custom sprite loading
-- ============================================================

local function oh_load_sprite(center_key, asset_key, mod_dir)
    -- Respect Balatro's texture scaling setting (1x or 2x)
    local scale = (G.SETTINGS and G.SETTINGS.GRAPHICS
                   and G.SETTINGS.GRAPHICS.texture_scaling) or 1
    local scale_dir = (scale == 2) and "2x" or "1x"
    local path = mod_dir .. "/assets/" .. scale_dir .. "/" .. asset_key .. ".png"

    if not love.filesystem.getInfo(path) then return false end

    -- Load with mipmaps + dpiscale to match Balatro's atlas loading
    local ok, img = pcall(love.graphics.newImage, path,
                          {mipmaps = true, dpiscale = scale})
    if not ok then
        print("[Open Heart] Failed to load sprite: " .. path)
        return false
    end

    -- Register single-sprite atlas (same structure as vanilla ASSET_ATLAS entries)
    local atlas_name = "oh_" .. asset_key
    G.ASSET_ATLAS[atlas_name] = {
        name = atlas_name,
        image = img,
        px = 71,
        py = 95,
    }

    -- Point center at our atlas
    if G.P_CENTERS[center_key] then
        G.P_CENTERS[center_key].atlas = atlas_name
        G.P_CENTERS[center_key].pos = { x = 0, y = 0 }
    end

    return true
end

-- ============================================================
-- Hook: Card.set_sprites — support custom atlas on centers
-- ============================================================
-- Vanilla set_sprites hardcodes G.ASSET_ATLAS[_center.set] for jokers on
-- initial sprite creation, ignoring _center.atlas. This post-hook fixes
-- the atlas after the original runs. (Same approach as Steamodded, but as
-- a lightweight wrapper instead of a full override.)

local original_set_sprites = Card.set_sprites

function Card:set_sprites(_center, _front)
    original_set_sprites(self, _center, _front)

    local center = _center or self.config.center
    if center and center.atlas and self.children.center then
        local custom_atlas = G.ASSET_ATLAS[center.atlas]
        if custom_atlas then
            self.children.center.atlas = custom_atlas
            self.children.center:set_sprite_pos(center.pos or {x = 0, y = 0})
        end
    end
end

-- Helper: parse localization entry the same way init_localization does
local function parse_loc_entry(entry)
    entry.text_parsed = {}
    for _, line in ipairs(entry.text or {}) do
        entry.text_parsed[#entry.text_parsed + 1] = loc_parse_string(line)
    end
    entry.name_parsed = {}
    for _, line in ipairs(type(entry.name) == 'table' and entry.name or {entry.name}) do
        entry.name_parsed[#entry.name_parsed + 1] = loc_parse_string(line)
    end
end

-- ============================================================
-- Hook: Game.set_language — add localization strings
-- ============================================================

local original_set_language = Game.set_language

function Game:set_language()
    original_set_language(self)

    G.localization.descriptions.Joker.j_calculator = {
        name = "Calculator",
        text = {
            "Sum ranks of scored cards",
            "({C:attention}A=14{}, K=13, Q=12, J=11)",
            "Even: {C:chips}+sum{} Chips",
            "Odd: {C:mult}+sum/2{} Mult",
        },
    }
    G.localization.descriptions.Joker.j_flashlight = {
        name = "Flashlight",
        text = {
            "First scored card",
            "gets {C:chips}X2{} Chips",
        },
    }
    G.localization.descriptions.Joker.j_fitness = {
        name = "Fitness Tracker",
        text = {
            "{C:chips}+1{} Chip for every",
            "card played this run",
            "{C:green}(Cap: {C:chips}150{C:green}, Currently {C:chips}+#1#{C:green}){}",
        },
    }
    G.localization.descriptions.Joker.j_camera = {
        name = "Camera",
        text = {
            "{C:mult}+25{} Mult if played hand",
            "matches previous hand type",
            "{C:green}(Photo: {C:attention}#1#{C:green}){}",
        },
    }
    G.localization.descriptions.Joker.j_maps = {
        name = "Maps",
        text = {
            "{C:mult}+#1#{} Mult if hand is a",
            "{C:attention}Straight{} or {C:attention}Straight Flush{}",
            "Bonus increases by {C:mult}+3{} each time",
            "Also earn {C:money}$2{}",
        },
    }
    G.localization.descriptions.Joker.j_alarm = {
        name = "Alarm Clock",
        text = {
            "{X:mult,C:white}X2{} Mult on",
            "{C:attention}last hand{} of round",
        },
    }
    G.localization.descriptions.Joker.j_playlist = {
        name = "Playlist",
        text = {
            "Playing same hand type",
            "consecutively builds streak:",
            "{X:mult,C:white}X1.5{}/{X:mult,C:white}X2{}/{X:mult,C:white}X2.5{} Mult",
            "{C:green}(Streak: {C:attention}#1#{C:green}){}",
        },
    }
    G.localization.descriptions.Back.b_smartphone = {
        name = "Smartphone Deck",
        text = {
            "Start run with",
            "{C:attention}Playlist{} joker ({C:attention}Eternal{})",
        },
    }

    parse_loc_entry(G.localization.descriptions.Joker.j_calculator)
    parse_loc_entry(G.localization.descriptions.Joker.j_flashlight)
    parse_loc_entry(G.localization.descriptions.Joker.j_fitness)
    parse_loc_entry(G.localization.descriptions.Joker.j_camera)
    parse_loc_entry(G.localization.descriptions.Joker.j_maps)
    parse_loc_entry(G.localization.descriptions.Joker.j_alarm)
    parse_loc_entry(G.localization.descriptions.Joker.j_playlist)
    parse_loc_entry(G.localization.descriptions.Back.b_smartphone)
end

-- ============================================================
-- Hook: Game.init_item_prototypes — register joker + deck
-- ============================================================

local original_init = Game.init_item_prototypes

function Game:init_item_prototypes()
    original_init(self)

    -- Register Calculator joker
    G.P_CENTERS.j_calculator = {
        key = "j_calculator",
        order = 200,
        unlocked = true,
        discovered = true,
        blueprint_compat = true,
        perishable_compat = true,
        eternal_compat = true,
        rarity = 1,
        cost = 4,
        name = "Calculator",
        pos = { x = 4, y = 1 },
        set = "Joker",
        config = {},
        cost_mult = 1.0,
    }
    table.insert(G.P_CENTER_POOLS.Joker, G.P_CENTERS.j_calculator)
    oh_load_sprite("j_calculator", "j_calculator", "Mods/PhoneDeck")

    -- Register Flashlight joker
    G.P_CENTERS.j_flashlight = {
        key = "j_flashlight",
        order = 201,
        unlocked = true,
        discovered = true,
        blueprint_compat = true,
        perishable_compat = true,
        eternal_compat = true,
        rarity = 1,
        cost = 4,
        name = "Flashlight",
        pos = { x = 4, y = 1 },
        set = "Joker",
        config = {},
        cost_mult = 1.0,
    }
    table.insert(G.P_CENTER_POOLS.Joker, G.P_CENTERS.j_flashlight)
    oh_load_sprite("j_flashlight", "j_flashlight", "Mods/PhoneDeck")

    -- Register Fitness Tracker joker
    G.P_CENTERS.j_fitness = {
        key = "j_fitness",
        order = 202,
        unlocked = true,
        discovered = true,
        blueprint_compat = true,
        perishable_compat = true,
        eternal_compat = true,
        rarity = 1,
        cost = 5,
        name = "Fitness Tracker",
        pos = { x = 4, y = 1 },
        set = "Joker",
        config = { extra = { chips = 0 } },
        cost_mult = 1.0,
    }
    table.insert(G.P_CENTER_POOLS.Joker, G.P_CENTERS.j_fitness)
    oh_load_sprite("j_fitness", "j_fitness", "Mods/PhoneDeck")

    -- Register Camera joker
    G.P_CENTERS.j_camera = {
        key = "j_camera",
        order = 203,
        unlocked = true,
        discovered = true,
        blueprint_compat = true,
        perishable_compat = true,
        eternal_compat = true,
        rarity = 2,
        cost = 6,
        name = "Camera",
        pos = { x = 4, y = 1 },
        set = "Joker",
        config = { extra = { last_hand = nil } },
        cost_mult = 1.0,
    }
    table.insert(G.P_CENTER_POOLS.Joker, G.P_CENTERS.j_camera)
    oh_load_sprite("j_camera", "j_camera", "Mods/PhoneDeck")

    -- Register Maps joker
    G.P_CENTERS.j_maps = {
        key = "j_maps",
        order = 204,
        unlocked = true,
        discovered = true,
        blueprint_compat = true,
        perishable_compat = true,
        eternal_compat = true,
        rarity = 2,
        cost = 6,
        name = "Maps",
        pos = { x = 4, y = 1 },
        set = "Joker",
        config = { extra = { bonus = 0 } },
        cost_mult = 1.0,
    }
    table.insert(G.P_CENTER_POOLS.Joker, G.P_CENTERS.j_maps)
    oh_load_sprite("j_maps", "j_maps", "Mods/PhoneDeck")

    -- Register Alarm Clock joker
    G.P_CENTERS.j_alarm = {
        key = "j_alarm",
        order = 205,
        unlocked = true,
        discovered = true,
        blueprint_compat = true,
        perishable_compat = true,
        eternal_compat = true,
        rarity = 2,
        cost = 5,
        name = "Alarm Clock",
        pos = { x = 4, y = 1 },
        set = "Joker",
        config = {},
        cost_mult = 1.0,
    }
    table.insert(G.P_CENTER_POOLS.Joker, G.P_CENTERS.j_alarm)
    oh_load_sprite("j_alarm", "j_alarm", "Mods/PhoneDeck")

    -- Register Playlist joker
    G.P_CENTERS.j_playlist = {
        key = "j_playlist",
        order = 206,
        unlocked = true,
        discovered = true,
        blueprint_compat = true,
        perishable_compat = true,
        eternal_compat = true,
        rarity = 3,
        cost = 8,
        name = "Playlist",
        pos = { x = 4, y = 1 },
        set = "Joker",
        config = { extra = { streak = 0, last_hand = nil } },
        cost_mult = 1.0,
    }
    table.insert(G.P_CENTER_POOLS.Joker, G.P_CENTERS.j_playlist)
    oh_load_sprite("j_playlist", "j_playlist", "Mods/PhoneDeck")

    -- Register Smartphone Deck back
    G.P_CENTERS.b_smartphone = {
        key = "b_smartphone",
        name = "Smartphone Deck",
        order = 20,
        unlocked = true,
        discovered = true,
        stake = 1,
        set = "Back",
        pos = { x = 0, y = 2 },
        config = {},
    }
    table.insert(G.P_CENTER_POOLS.Back, G.P_CENTERS.b_smartphone)
end

-- ============================================================
-- Hook: Back.apply_to_run — grant Fitness Tracker on run start
-- ============================================================

local original_apply = Back.apply_to_run

function Back:apply_to_run()
    original_apply(self)

    if self.effect.center.key == "b_smartphone" then
        G.E_MANAGER:add_event(Event({
            func = function()
                local card = add_joker("j_playlist", nil, nil, true)
                card.ability.eternal = true
                return true
            end,
        }))
    end
end

-- ============================================================
-- Hook: Card.calculate_joker — PhoneDeck scoring
-- ============================================================

local original_calc = Card.calculate_joker

function Card:calculate_joker(context)
    if self.ability.set ~= "Joker" then return original_calc(self, context) end
    local key = self.config.center.key

    -- Fitness Tracker: accumulate cards played, cap at 150 (pre-scoring hook)
    if key == "j_fitness" and context.before then
        self.ability.extra.chips = math.min(150, self.ability.extra.chips + #context.full_hand)
    end

    -- Flashlight: first scored card gets X2 chips (per-card hook)
    if key == "j_flashlight" and context.individual
       and context.cardarea == G.play then
        if context.other_card == context.scoring_hand[1] then
            return {
                chips = context.other_card.base.nominal or 0,
                card = self,
            }
        end
    end

    -- Camera: +25 Mult if hand matches the photo (main scoring hook)
    if key == "j_camera" and context.joker_main then
        local current_hand = G.GAME.last_hand_played
        if self.ability.extra.last_hand and current_hand == self.ability.extra.last_hand then
            return {
                mult_mod = 25,
                message = localize({ type = "variable", key = "a_mult", vars = { 25 } }),
                colour = G.C.MULT,
                card = self,
            }
        end
    end

    -- Playlist: XMult streak for consecutive same hand type
    if key == "j_playlist" and context.joker_main then
        local current_hand = G.GAME.last_hand_played
        local streak = self.ability.extra.streak
        -- Compute prospective streak: does current hand match last?
        if self.ability.extra.last_hand and current_hand == self.ability.extra.last_hand then
            streak = streak + 1
        else
            streak = 0
        end
        local STREAK_XMULT = { [0] = 1.0, [1] = 1.5, [2] = 2.0 }
        local xm = STREAK_XMULT[streak] or 2.5
        -- Store prospective streak for after hook to commit
        self.ability.extra._pending_streak = streak
        self.ability.extra._pending_hand = current_hand
        if xm > 1 then
            return {
                Xmult_mod = xm,
                message = localize({ type = "variable", key = "a_xmult", vars = { xm } }),
                colour = G.C.MULT,
                card = self,
            }
        end
    end

    -- Alarm Clock: X2 Mult on last hand of round
    if key == "j_alarm" and context.joker_main then
        if G.GAME.current_round.hands_left == 0 then
            return {
                Xmult_mod = 2,
                message = localize({ type = "variable", key = "a_xmult", vars = { 2 } }),
                colour = G.C.MULT,
                card = self,
            }
        end
    end

    -- Maps: +20 Mult (scaling) on Straights/Straight Flushes, +$2
    if key == "j_maps" and context.joker_main then
        local hand = G.GAME.last_hand_played
        if hand == "Straight" or hand == "Straight Flush" then
            local total = 20 + self.ability.extra.bonus
            self.ability.extra.bonus = self.ability.extra.bonus + 3
            return {
                mult_mod = total,
                message = localize({ type = "variable", key = "a_mult", vars = { total } }),
                colour = G.C.MULT,
                card = self,
                dollars = 2,
            }
        end
    end

    -- Fitness Tracker: score accumulated chips (main scoring hook)
    if key == "j_fitness" and context.joker_main then
        if self.ability.extra.chips > 0 then
            return {
                chip_mod = self.ability.extra.chips,
                message = localize({ type = "variable", key = "a_chips", vars = { self.ability.extra.chips } }),
                colour = G.C.CHIPS,
                card = self,
            }
        end
    end

    if key == "j_calculator" then
        if context.joker_main then
            -- Sum ranks: A=14, K=13, Q=12, J=11, number cards = face value
            local rank_sum = 0
            for _, card in ipairs(context.scoring_hand) do
                rank_sum = rank_sum + card:get_id()
            end

            if rank_sum % 2 == 0 then
                return {
                    chip_mod = rank_sum,
                    message = localize({ type = "variable", key = "a_chips", vars = { rank_sum } }),
                    colour = G.C.CHIPS,
                    card = self,
                }
            else
                local half = math.floor(rank_sum / 2)
                return {
                    mult_mod = half,
                    message = localize({ type = "variable", key = "a_mult", vars = { half } }),
                    colour = G.C.MULT,
                    card = self,
                }
            end
        end
    end

    -- Playlist: commit streak after scoring (post-scoring hook)
    if key == "j_playlist" and context.after then
        if self.ability.extra._pending_streak then
            self.ability.extra.streak = self.ability.extra._pending_streak
            self.ability.extra.last_hand = self.ability.extra._pending_hand
            self.ability.extra._pending_streak = nil
            self.ability.extra._pending_hand = nil
        end
    end

    -- Camera: update photo after scoring (post-scoring hook)
    if key == "j_camera" and context.after then
        self.ability.extra.last_hand = G.GAME.last_hand_played
    end

    return original_calc(self, context)
end

-- ============================================================
-- Hook: Card.generate_UIBox_ability_table — dynamic tooltips
-- ============================================================

local original_gen_ui = Card.generate_UIBox_ability_table

function Card:generate_UIBox_ability_table()
    local key = self.config.center.key
    if key == "j_fitness" then
        local desc = G.localization.descriptions.Joker.j_fitness
        if desc then
            local chips = self.ability.extra and self.ability.extra.chips or 0
            desc.text[3] = "{C:green}(Cap: {C:chips}150{C:green}, Currently {C:chips}+" .. chips .. "{C:green}){}"
            desc.text_parsed[3] = loc_parse_string(desc.text[3])
        end
    elseif key == "j_maps" then
        local desc = G.localization.descriptions.Joker.j_maps
        if desc then
            local total = 20 + (self.ability.extra and self.ability.extra.bonus or 0)
            desc.text[1] = "{C:mult}+" .. total .. "{} Mult if hand is a"
            desc.text_parsed[1] = loc_parse_string(desc.text[1])
        end
    elseif key == "j_playlist" then
        local desc = G.localization.descriptions.Joker.j_playlist
        if desc then
            local streak = self.ability.extra and self.ability.extra.streak or 0
            desc.text[4] = "{C:green}(Streak: {C:attention}" .. streak .. "{C:green}){}"
            desc.text_parsed[4] = loc_parse_string(desc.text[4])
        end
    elseif key == "j_camera" then
        local desc = G.localization.descriptions.Joker.j_camera
        if desc then
            local photo = (self.ability.extra and self.ability.extra.last_hand) or "None"
            desc.text[3] = "{C:green}(Photo: {C:attention}" .. photo .. "{C:green}){}"
            desc.text_parsed[3] = loc_parse_string(desc.text[3])
        end
    end
    return original_gen_ui(self)
end
