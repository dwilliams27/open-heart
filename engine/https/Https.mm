#include "common/config.h"
#include "Https.h"
#include "common/Exception.h"

#ifdef LOVE_MACOSX

#import <Foundation/Foundation.h>

namespace love
{
namespace https
{

Https::Https()
{
}

HttpsRequest *Https::request(const std::string &url, const std::string &method,
	const std::map<std::string, std::string> &headers,
	const std::string &body, double timeout)
{
	// Enforce HTTPS-only.
	if (url.find("https://") != 0)
		throw love::Exception("love.https only supports https:// URLs (got: %s)", url.c_str());

	HttpsRequest *req = new HttpsRequest();

	// Retain for the async block — released in the completion handler.
	req->retain();

	@autoreleasepool
	{
		NSString *nsUrl = [NSString stringWithUTF8String:url.c_str()];
		NSURL *nsUrlObj = [NSURL URLWithString:nsUrl];

		if (nsUrlObj == nil)
		{
			req->setError("Invalid URL");
			req->release();
			return req;
		}

		NSMutableURLRequest *nsRequest = [NSMutableURLRequest requestWithURL:nsUrlObj];
		[nsRequest setHTTPMethod:[NSString stringWithUTF8String:method.c_str()]];

		if (timeout > 0)
			[nsRequest setTimeoutInterval:timeout];

		for (auto &pair : headers)
		{
			NSString *key = [NSString stringWithUTF8String:pair.first.c_str()];
			NSString *val = [NSString stringWithUTF8String:pair.second.c_str()];
			[nsRequest setValue:val forHTTPHeaderField:key];
		}

		if (!body.empty())
		{
			NSData *bodyData = [NSData dataWithBytes:body.c_str() length:body.size()];
			[nsRequest setHTTPBody:bodyData];
		}

		NSURLSessionConfiguration *config = [NSURLSessionConfiguration ephemeralSessionConfiguration];
		NSURLSession *session = [NSURLSession sessionWithConfiguration:config];

		NSURLSessionDataTask *task = [session dataTaskWithRequest:nsRequest
			completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
				if (error != nil)
				{
					req->setError(error.localizedDescription.UTF8String);
				}
				else
				{
					NSHTTPURLResponse *httpResponse = (NSHTTPURLResponse *)response;
					int statusCode = (int)httpResponse.statusCode;

					std::string responseBody;
					if (data != nil)
						responseBody = std::string((const char *)data.bytes, data.length);

					std::map<std::string, std::string> responseHeaders;
					NSDictionary *allHeaders = httpResponse.allHeaderFields;
					for (NSString *key in allHeaders)
					{
						NSString *val = allHeaders[key];
						responseHeaders[[key UTF8String]] = [val UTF8String];
					}

					req->setResponse(statusCode, responseBody, responseHeaders);
				}

				req->release();
			}];

		[task resume];
	}

	return req;
}

} // https
} // love

#endif // LOVE_MACOSX
