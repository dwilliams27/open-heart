-- WeatherDeck — Open Heart gameplay mod
-- Custom deck that starts with "The Weatherman" joker.
-- Fetches real weather via wttr.in and applies scoring bonuses.

if not love.https then return end

-- ============================================================
-- Weather state
-- ============================================================

local weather = {
    state = "mild",      -- rain | snow | warm | cold | mild
    desc = "Checking...", -- human-readable for tooltip
    timer = 60,          -- start at 60 so first fetch fires immediately
    req = nil,
}

-- ============================================================
-- Weather classification
-- ============================================================

local SNOW_CODES = {}
for _, c in ipairs({179, 227, 230,
    323, 326, 329, 332, 335, 338,
    368, 371, 374, 377}) do
    SNOW_CODES[c] = true
end

local RAIN_CODES = {}
for _, c in ipairs({176,
    263, 266, 281, 284,
    293, 296, 299, 302, 305, 308, 311, 314,
    353, 356, 359}) do
    RAIN_CODES[c] = true
end

local function c_to_f(c) return math.floor(c * 9 / 5 + 32 + 0.5) end

local function classify_weather(code, temp)
    local temp_f = temp and c_to_f(temp)
    if code and SNOW_CODES[code] then
        return "snow", "Snowing"
    elseif code and RAIN_CODES[code] then
        return "rain", "Raining"
    elseif temp_f and temp_f > 60 then
        return "warm", "Warm (" .. temp_f .. "\xC2\xB0F)"
    elseif temp_f and temp_f <= 32 then
        return "cold", "Cold (" .. temp_f .. "\xC2\xB0F)"
    else
        local label = "Mild"
        if temp_f then label = label .. " (" .. temp_f .. "\xC2\xB0F)" end
        return "mild", label
    end
end

local function effect_text(state)
    if state == "rain" then return "+4 Mult/card"
    elseif state == "snow" then return "+100 Chips"
    elseif state == "warm" then return "X1.5 Mult"
    elseif state == "cold" then return "+20 Mult"
    else return "+4 Mult"
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

    G.localization.descriptions.Joker.j_weatherman = {
        name = "The Weatherman",
        text = {
            "Gives a bonus based on",
            "the local weather",
            "{C:green}#1#{}",
        },
    }
    G.localization.descriptions.Back.b_weather = {
        name = "Weather Deck",
        text = {
            "Start run with",
            "{C:attention}The Weatherman{} joker",
        },
    }

    -- Parse our entries (init_localization already ran for vanilla strings)
    parse_loc_entry(G.localization.descriptions.Joker.j_weatherman)
    parse_loc_entry(G.localization.descriptions.Back.b_weather)
end

-- ============================================================
-- Hook: Game.init_item_prototypes — register joker + deck
-- ============================================================

local original_init = Game.init_item_prototypes

function Game:init_item_prototypes()
    original_init(self)

    -- Register The Weatherman joker
    -- .key is required — vanilla entries get it from the k,v loop in
    -- init_item_prototypes, but our entries are added after that loop.
    G.P_CENTERS.j_weatherman = {
        key = "j_weatherman",
        order = 200,
        unlocked = true,
        discovered = true,
        blueprint_compat = true,
        perishable_compat = true,
        eternal_compat = true,
        rarity = 2,
        cost = 6,
        name = "The Weatherman",
        pos = { x = 4, y = 1 },
        set = "Joker",
        config = {},
        cost_mult = 1.0,
    }
    table.insert(G.P_CENTER_POOLS.Joker, G.P_CENTERS.j_weatherman)

    -- Register Weather Deck back
    G.P_CENTERS.b_weather = {
        key = "b_weather",
        name = "Weather Deck",
        order = 20,
        unlocked = true,
        discovered = true,
        stake = 1,
        set = "Back",
        pos = { x = 0, y = 2 },
        config = {},
    }
    table.insert(G.P_CENTER_POOLS.Back, G.P_CENTERS.b_weather)
end

-- ============================================================
-- Hook: Back.apply_to_run — grant The Weatherman on run start
-- ============================================================

local original_apply = Back.apply_to_run

function Back:apply_to_run()
    original_apply(self)

    if self.effect.center.key == "b_weather" then
        G.E_MANAGER:add_event(Event({
            func = function()
                local card = add_joker("j_weatherman", nil, nil, true)
                card.ability.eternal = true
                return true
            end,
        }))
    end
end

-- ============================================================
-- Hook: Card.calculate_joker — weather-based scoring
-- ============================================================

local original_calc = Card.calculate_joker

function Card:calculate_joker(context)
    if self.ability.set == "Joker" and self.config.center.key == "j_weatherman" then
        -- Rain: per-card mult in the individual scoring phase
        if weather.state == "rain" and context.individual
           and context.cardarea == G.play then
            return {
                mult = 4,
                card = self,
            }
        end

        -- All other weather: main scoring phase
        if context.joker_main then
            if weather.state == "snow" then
                return {
                    chip_mod = 100,
                    message = localize({ type = "variable", key = "a_chips", vars = { 100 } }),
                    colour = G.C.CHIPS,
                    card = self,
                }
            elseif weather.state == "warm" then
                return {
                    Xmult_mod = 1.5,
                    message = localize({ type = "variable", key = "a_xmult", vars = { 1.5 } }),
                    colour = G.C.MULT,
                    card = self,
                }
            elseif weather.state == "cold" then
                return {
                    mult_mod = 20,
                    message = localize({ type = "variable", key = "a_mult", vars = { 20 } }),
                    colour = G.C.MULT,
                    card = self,
                }
            else -- mild / offline / unknown
                return {
                    mult_mod = 4,
                    message = localize({ type = "variable", key = "a_mult", vars = { 4 } }),
                    colour = G.C.MULT,
                    card = self,
                }
            end
        end
    end

    return original_calc(self, context)
end

-- ============================================================
-- Hook: Card.generate_UIBox_ability_table — dynamic tooltip
-- ============================================================

local original_gen_ui = Card.generate_UIBox_ability_table

function Card:generate_UIBox_ability_table()
    if self.config.center.key == "j_weatherman" then
        local info = weather.desc .. " \xE2\x80\x94 " .. effect_text(weather.state)
        -- Re-parse the third line so the tooltip reflects current weather
        local desc = G.localization.descriptions.Joker.j_weatherman
        if desc then
            desc.text[3] = "{C:green}" .. info .. "{}"
            desc.text_parsed[3] = loc_parse_string(desc.text[3])
        end
    end
    return original_gen_ui(self)
end

-- ============================================================
-- Hook: Game.update — weather fetch timer + polling
-- ============================================================

local original_update = Game.update

function Game:update(dt)
    original_update(self, dt)

    -- Tick the timer
    weather.timer = weather.timer + dt

    -- Fire a new request every 60 seconds
    if weather.timer >= 60 and not weather.req then
        weather.timer = 0
        local ok, r = pcall(love.https.request, "https://wttr.in/?format=j1")
        if ok then
            weather.req = r
        end
    end

    -- Poll for response
    if weather.req and weather.req:isComplete() then
        local status, body = weather.req:getResponse()
        weather.req = nil

        if status == 200 and body then
            local code = tonumber(body:match('"weatherCode"%s*:%s*"(%d+)"'))
            local temp = tonumber(body:match('"temp_C"%s*:%s*"(-?%d+)"'))
            weather.state, weather.desc = classify_weather(code, temp)
        else
            weather.state = "mild"
            weather.desc = "Offline"
        end
    end
end
