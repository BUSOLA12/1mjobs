import logging
import json
from datetime import datetime

logger = logging.getLogger("request_debugger")

class RequestDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            log_data = {
                "time": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.get_full_path(),
                "remote_ip": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "user": str(getattr(request, "user", None)),
                "is_authenticated": getattr(request, "user", None) and request.user.is_authenticated,
                "cookies": list(request.COOKIES.keys()),
                "headers": {
                    "Authorization": "SET" if request.META.get("HTTP_AUTHORIZATION") else "NONE",
                    "Origin": request.META.get("HTTP_ORIGIN"),
                    "Host": request.META.get("HTTP_HOST"),
                    "Referer": request.META.get("HTTP_REFERER"),
                    "ContentType": request.META.get("CONTENT_TYPE"),
                }
            }


            logger.info(json.dumps(log_data))

        except Exception as e:
            logger.error(f"Request debug middleware failed: {e}")

        return self.get_response(request)
