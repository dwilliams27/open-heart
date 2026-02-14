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
    G.localization.descriptions.Back.b_smartphone = {
        name = "Smartphone Deck",
        text = {
            "Start run with",
            "{C:attention}Flashlight{} joker ({C:attention}Eternal{})",
        },
    }

    parse_loc_entry(G.localization.descriptions.Joker.j_calculator)
    parse_loc_entry(G.localization.descriptions.Joker.j_flashlight)
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
-- Hook: Back.apply_to_run — grant Flashlight on run start
-- ============================================================

local original_apply = Back.apply_to_run

function Back:apply_to_run()
    original_apply(self)

    if self.effect.center.key == "b_smartphone" then
        G.E_MANAGER:add_event(Event({
            func = function()
                local card = add_joker("j_flashlight", nil, nil, true)
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

    return original_calc(self, context)
end
