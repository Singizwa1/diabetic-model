"""Redis cache and token storage configuration."""

import json
from typing import Optional, Dict, Any

import redis
from redis.exceptions import RedisError

from app.core.config import get_settings

settings = get_settings()


class RedisUnavailableError(Exception):
    """Raised when Redis cannot be reached for token/session operations."""


def _parse_int(value: Any, default: int) -> int:
    """Safely parse integer values from environment-like settings."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


redis_client = redis.Redis(
    host=settings.REDIS_HOST or "localhost",
    port=_parse_int(settings.REDIS_PORT, 6379),
    db=_parse_int(settings.REDIS_DB, 0),
    password=settings.REDIS_PASSWORD or None,
    username=settings.REDIS_USERNAME or None,
    ssl=bool(settings.REDIS_SSL),
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True,
)


class TokenManager:
    """Manage JWT sessions and blacklist entries in Redis."""

    SESSION_PREFIX = "jwt:"
    BLACKLIST_PREFIX = "blacklist:"

    @staticmethod
    def store_session(jti: str, token_payload: Dict[str, Any], ttl_seconds: int) -> bool:
        """Store JWT payload by JTI with TTL."""
        redis_key = f"{TokenManager.SESSION_PREFIX}{jti}"
        try:
            return bool(redis_client.setex(redis_key, ttl_seconds, json.dumps(token_payload)))
        except RedisError as exc:
            raise RedisUnavailableError("Unable to store token session in Redis") from exc

    @staticmethod
    def get_session(jti: str) -> Optional[Dict[str, Any]]:
        """Get JWT payload from Redis by JTI."""
        redis_key = f"{TokenManager.SESSION_PREFIX}{jti}"
        try:
            data = redis_client.get(redis_key)
        except RedisError as exc:
            raise RedisUnavailableError("Unable to read token session from Redis") from exc
        if not data:
            return None
        return json.loads(data)

    @staticmethod
    def is_session_active(jti: str) -> bool:
        """Check if JWT session exists in Redis."""
        redis_key = f"{TokenManager.SESSION_PREFIX}{jti}"
        try:
            return bool(redis_client.exists(redis_key))
        except RedisError as exc:
            raise RedisUnavailableError("Unable to verify token session in Redis") from exc

    @staticmethod
    def remove_session(jti: str) -> bool:
        """Remove JWT session by JTI."""
        redis_key = f"{TokenManager.SESSION_PREFIX}{jti}"
        try:
            return bool(redis_client.delete(redis_key))
        except RedisError as exc:
            raise RedisUnavailableError("Unable to remove token session from Redis") from exc

    @staticmethod
    def blacklist_token(token: str, ttl_seconds: int = 24 * 60 * 60) -> bool:
        """Blacklist full token string with TTL for immediate logout/revocation."""
        redis_key = f"{TokenManager.BLACKLIST_PREFIX}{token}"
        try:
            return bool(redis_client.setex(redis_key, ttl_seconds, "true"))
        except RedisError as exc:
            raise RedisUnavailableError("Unable to blacklist token in Redis") from exc

    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Check whether token is blacklisted."""
        redis_key = f"{TokenManager.BLACKLIST_PREFIX}{token}"
        try:
            return bool(redis_client.exists(redis_key))
        except RedisError as exc:
            raise RedisUnavailableError("Unable to check token blacklist in Redis") from exc


def check_redis_connection():
    """Check if Redis is connected."""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        return False
