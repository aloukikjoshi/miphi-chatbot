import time, traceback
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.logger import get_logger, log_crash

logger = get_logger('miphi.middleware')

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        try:
            response = await call_next(request)
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info('%s %s', request.method, request.url.path, extra={'user_id': None, 'session_id': None, 'latency_ms': latency_ms, 'status_code': response.status_code})
            return response
        except Exception as exc:
            log_crash(exc)
            return JSONResponse(status_code=500, content={'detail': 'Internal server error.'})

def setup_cors(app):
    app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
