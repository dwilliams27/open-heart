#include "HttpsRequest.h"

namespace love
{
namespace https
{

love::Type HttpsRequest::type("HttpsRequest", &Object::type);

HttpsRequest::HttpsRequest()
	: complete(false)
	, statusCode(0)
{
}

bool HttpsRequest::isComplete()
{
	std::lock_guard<std::mutex> lock(mutex);
	return complete;
}

int HttpsRequest::getStatusCode()
{
	std::lock_guard<std::mutex> lock(mutex);
	return statusCode;
}

std::string HttpsRequest::getBody()
{
	std::lock_guard<std::mutex> lock(mutex);
	return body;
}

std::map<std::string, std::string> HttpsRequest::getHeaders()
{
	std::lock_guard<std::mutex> lock(mutex);
	return headers;
}

void HttpsRequest::setResponse(int statusCode, const std::string &body, const std::map<std::string, std::string> &headers)
{
	std::lock_guard<std::mutex> lock(mutex);
	this->statusCode = statusCode;
	this->body = body;
	this->headers = headers;
	this->complete = true;
}

void HttpsRequest::setError(const std::string &message)
{
	std::lock_guard<std::mutex> lock(mutex);
	this->statusCode = 0;
	this->body = message;
	this->complete = true;
}

} // https
} // love
