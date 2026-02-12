#pragma once

#include "common/Module.h"
#include "HttpsRequest.h"

#include <string>
#include <map>

namespace love
{
namespace https
{

class Https : public Module
{
public:

	Https();
	virtual ~Https() {}

	// Implements Module.
	ModuleType getModuleType() const override { return M_HTTPS; }
	const char *getName() const override { return "love.https"; }

	HttpsRequest *request(const std::string &url, const std::string &method,
		const std::map<std::string, std::string> &headers,
		const std::string &body, double timeout);

}; // Https

} // https
} // love
