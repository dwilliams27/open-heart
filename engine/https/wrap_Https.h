#pragma once

#include "common/runtime.h"
#include "Https.h"

namespace love
{
namespace https
{

extern "C" LOVE_EXPORT int luaopen_love_https(lua_State *L);

} // https
} // love
