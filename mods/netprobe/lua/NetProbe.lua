-- NetProbe — Open Heart branding mod
-- Displays OpenHeart version on the main menu

local original_version = nil

-- Hook Game:main_menu to replace the version string
local original_main_menu = Game.main_menu

function Game:main_menu(change)
    if not original_version then original_version = G.VERSION end
    G.VERSION = original_version .. " | OpenHeart 0.1 - Made By FarmerBilly27"
    return original_main_menu(self, change)
end
