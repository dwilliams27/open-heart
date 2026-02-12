#pragma once

#include "common/Object.h"

#include <string>
#include <map>
#include <mutex>

namespace love
{
namespace https
{

class HttpsRequest : public love::Object
{
public:

	static love::Type type;

	HttpsRequest();
	virtual ~HttpsRequest() {}

	bool isComplete();
	int getStatusCode();
	std::string getBody();
	std::map<std::string, std::string> getHeaders();

	void setResponse(int statusCode, const std::string &body, const std::map<std::string, std::string> &headers);
	void setError(const std::string &message);

private:

	std::mutex mutex;
	bool complete;
	int statusCode;
	std::string body;
	std::map<std::string, std::string> headers;

}; // HttpsRequest

} // https
} // love
