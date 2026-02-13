-- Example mod: validates that engine modules are available
local function init()
    if love and love.https then
        print("[Example] love.https is available")
    else
        print("[Example] love.https is NOT available")
    end
end

init()
