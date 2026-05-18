from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from legal_agent.disclaimer import inject_disclaimer


async def disclaimer_middleware(request: Request, call_next):
    response = await call_next(request)
    if isinstance(response, JSONResponse):
        body = response.body
        try:
            data = response.json()
        except Exception:
            return response

        if isinstance(data, dict):
            response.body = JSONResponse(inject_disclaimer(data)).body
    return response
