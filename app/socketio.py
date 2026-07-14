import socketio

from app.core.security import verify_token
from app.infrastructure.logging import create_logger

logger = create_logger("socketio")

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=[])


@sio.event
async def connect(sid, environ, auth):
    try:
        token = auth.get("token") if auth else None
        if not token:
            raise ConnectionRefusedError("Authentication required")
        payload = verify_token(token)
        async with sio.session(sid) as session:
            session["user_id"] = payload.get("id")
            session["user_role"] = payload.get("role")
        logger.info("socket_connected", sid=sid, user_id=payload.get("id"))
    except Exception as e:
        logger.warning("socket_auth_failed", sid=sid, error=str(e))
        raise ConnectionRefusedError("Authentication failed")


@sio.event
async def disconnect(sid):
    logger.info("socket_disconnected", sid=sid)
