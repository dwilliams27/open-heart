-- NetProbe — Open Heart proof-of-concept mod
-- Fetches your public IP via love.https and displays it on the main menu

if not love.https then return end

local req = nil
local net_text = "Connecting..."
local original_version = nil

-- Fire the HTTPS request on load
local ok, result = pcall(love.https.request, "https://httpbin.org/ip")
if ok then
    req = result
else
    return
end

-- Hook Game:main_menu to append network status to the version string
local original_main_menu = Game.main_menu

function Game:main_menu(change)
    if not original_version then original_version = G.VERSION end
    G.VERSION = original_version .. " | " .. net_text
    return original_main_menu(self, change)
end

-- Hook Game:update to poll the HTTPS request
local original_game_update = Game.update

function Game:update(dt)
    original_game_update(self, dt)
    if req and req:isComplete() then
        local status, body = req:getResponse()
        if status == 200 then
            local ip = body:match('"origin":%s*"([^"]+)"')
            net_text = ip and ("Connected: " .. ip) or "Connected"
        else
            net_text = "Offline"
        end
        req = nil
        if original_version then
            G.VERSION = original_version .. " | " .. net_text
        end
    end
end
