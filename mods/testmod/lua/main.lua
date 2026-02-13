-- TestMod: visual proof that the modular build system + love.https works
-- Fetches your public IP from httpbin.org and displays it on screen.

local req = nil
local result_text = ""
local status_text = "Requesting..."
local phase = "loading"
local elapsed = 0

function love.load()
    love.window.setTitle("Open Heart — TestMod")
    love.window.setMode(640, 360)
    love.graphics.setBackgroundColor(0.08, 0.08, 0.12)

    local ok, result = pcall(love.https.request, "https://httpbin.org/ip")
    if ok then
        req = result
        phase = "fetching"
    else
        result_text = "love.https.request() failed"
        status_text = tostring(result)
        phase = "error"
    end
end

function love.update(dt)
    elapsed = elapsed + dt

    if phase == "fetching" and req and req:isComplete() then
        local status, body, headers = req:getResponse()
        if status == 200 then
            local origin = body:match('"origin":%s*"([^"]+)"')
            if origin then
                result_text = origin
                status_text = "HTTP 200 OK — " .. #body .. " bytes"
                phase = "done"
            else
                result_text = "Couldn't parse response"
                status_text = body:sub(1, 120)
                phase = "error"
            end
        else
            result_text = "Request failed"
            status_text = "HTTP " .. tostring(status) .. " — " .. tostring(body):sub(1, 120)
            phase = "error"
        end
        req = nil
    end

    if phase == "fetching" and elapsed > 15 then
        result_text = "Timed out (15s)"
        status_text = "No response from server"
        phase = "error"
        req = nil
    end
end

function love.draw()
    local w = love.graphics.getWidth()

    -- Title
    love.graphics.setColor(1, 1, 1)
    love.graphics.printf("Open Heart — TestMod", 0, 40, w, "center")

    -- Subtitle
    love.graphics.setColor(0.6, 0.6, 0.7)
    love.graphics.printf("Fetching your public IP via love.https", 0, 70, w, "center")

    -- Separator
    love.graphics.setColor(0.3, 0.3, 0.4)
    love.graphics.line(80, 105, w - 80, 105)

    if phase == "fetching" then
        love.graphics.setColor(1, 0.8, 0.2)
        local dots = string.rep(".", (math.floor(elapsed * 2) % 4))
        love.graphics.printf("Fetching" .. dots, 0, 140, w, "center")
    elseif phase == "done" then
        love.graphics.setColor(0.6, 0.6, 0.7)
        love.graphics.printf("Your public IP address:", 0, 125, w, "center")

        love.graphics.setColor(0.2, 1, 0.4)
        love.graphics.printf(result_text, 0, 155, w, "center")

        love.graphics.setColor(0.5, 0.5, 0.6)
        love.graphics.printf(status_text, 0, 185, w, "center")

        love.graphics.setColor(0.4, 0.8, 1)
        love.graphics.printf("Fetched live from httpbin.org/ip", 0, 225, w, "center")
        love.graphics.printf("via love.https (NSURLSession engine module)", 0, 245, w, "center")
    elseif phase == "error" then
        love.graphics.setColor(1, 0.3, 0.3)
        love.graphics.printf(result_text, 0, 140, w, "center")
        love.graphics.setColor(0.6, 0.4, 0.4)
        love.graphics.printf(status_text, 0, 170, w, "center")
    end

    love.graphics.setColor(0.3, 0.3, 0.35)
    love.graphics.printf("LÖVE " .. love._version .. " • Press Escape to quit", 0, 320, w, "center")
end

function love.keypressed(key)
    if key == "escape" then
        love.event.quit()
    end
end
