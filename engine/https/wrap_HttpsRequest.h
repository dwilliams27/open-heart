#pragma once

#include "common/runtime.h"
#include "HttpsRequest.h"

namespace love
{
namespace https
{

extern int luaopen_httpsrequest(lua_State *L);

} // https
} // love
