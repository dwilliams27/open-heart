#include "wrap_HttpsRequest.h"

namespace love
{
namespace https
{

static HttpsRequest *luax_checkhttpsrequest(lua_State *L, int idx)
{
	return luax_checktype<HttpsRequest>(L, idx);
}

int w_HttpsRequest_isComplete(lua_State *L)
{
	HttpsRequest *req = luax_checkhttpsrequest(L, 1);
	luax_pushboolean(L, req->isComplete());
	return 1;
}

int w_HttpsRequest_getResponse(lua_State *L)
{
	HttpsRequest *req = luax_checkhttpsrequest(L, 1);

	if (!req->isComplete())
		return luaL_error(L, "Request is not yet complete.");

	lua_pushinteger(L, req->getStatusCode());
	lua_pushlstring(L, req->getBody().c_str(), req->getBody().size());

	std::map<std::string, std::string> headers = req->getHeaders();
	lua_newtable(L);
	for (auto &pair : headers)
	{
		lua_pushlstring(L, pair.second.c_str(), pair.second.size());
		lua_setfield(L, -2, pair.first.c_str());
	}

	return 3;
}

static const luaL_Reg w_HttpsRequest_functions[] =
{
	{ "isComplete", w_HttpsRequest_isComplete },
	{ "getResponse", w_HttpsRequest_getResponse },
	{ 0, 0 }
};

int luaopen_httpsrequest(lua_State *L)
{
	luax_register_type(L, &HttpsRequest::type, w_HttpsRequest_functions, nullptr);
	return 0;
}

} // https
} // love
