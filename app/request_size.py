
from starlette.responses import JSONResponse


class RequestSizeLimitMiddleware:
    def __init__(self, app, max_body_size=1024 * 1024):
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def reject():
            response = JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
            await response(scope, receive, send)

        # Reject requests that declare an excessive body size.
        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")

        if content_length is not None:
            try:
                if int(content_length) > self.max_body_size:
                    await reject()
                    return
            except ValueError:
                pass

        # Also check the actual bytes received.
        # This protects requests without Content-Length.
        messages = []
        total_size = 0

        while True:
            message = await receive()

            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                continue

            total_size += len(message.get("body", b""))

            if total_size > self.max_body_size:
                await reject()
                return

            messages.append(message)

            if not message.get("more_body", False):
                break

        # Replay the body to FastAPI after validation.
        async def replay_receive():
            if messages:
                return messages.pop(0)
            return await receive()

        await self.app(scope, replay_receive, send)
