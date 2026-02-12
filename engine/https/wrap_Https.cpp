#include "common/config.h"

#include "wrap_Https.h"
#include "wrap_HttpsRequest.h"

namespace love
{
namespace https
{

#define instance() (Module::getInstance<Https>(Module::M_HTTPS))

int w_request(lua_State *L)
{
	std::string url = luaL_checkstring(L, 1);
	std::string method = "GET";
	std::map<std::string, std::string> headers;
	std::string body;
	double timeout = 30.0;

	if (lua_istable(L, 2))
	{
		lua_getfield(L, 2, "method");
		if (!lua_isnoneornil(L, -1))
			method = luaL_checkstring(L, -1);
		lua_pop(L, 1);

		lua_getfield(L, 2, "body");
		if (!lua_isnoneornil(L, -1))
			body = luaL_checkstring(L, -1);
		lua_pop(L, 1);

		lua_getfield(L, 2, "timeout");
		if (!lua_isnoneornil(L, -1))
			timeout = luaL_checknumber(L, -1);
		lua_pop(L, 1);

		lua_getfield(L, 2, "headers");
		if (lua_istable(L, -1))
		{
			lua_pushnil(L);
			while (lua_next(L, -2) != 0)
			{
				const char *key = lua_tostring(L, -2);
				const char *val = lua_tostring(L, -1);
				if (key && val)
					headers[key] = val;
				lua_pop(L, 1);
			}
		}
		lua_pop(L, 1);
	}

	HttpsRequest *req = nullptr;
	luax_catchexcept(L, [&]() { req = instance()->request(url, method, headers, body, timeout); });
	luax_pushtype(L, req);
	req->release();
	return 1;
}

static const luaL_Reg functions[] =
{
	{ "request", w_request },
	{ 0, 0 }
};

static const lua_CFunction types[] =
{
	luaopen_httpsrequest,
	nullptr
};

extern "C" int luaopen_love_https(lua_State *L)
{
	Https *inst = instance();
	if (inst == nullptr)
	{
		luax_catchexcept(L, [&](){ inst = new Https(); });
	}
	else
		inst->retain();

	WrappedModule w;
	w.module = inst;
	w.name = "https";
	w.type = &Module::type;
	w.functions = functions;
	w.types = types;

	return luax_register_module(L, w);
}

} // https
} // love
