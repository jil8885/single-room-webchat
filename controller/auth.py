from datetime import datetime, timezone, timedelta
import aioredis
import jwt

import config

TZ_UTC = timezone(timedelta(hours=0))
_USER_LOGIN_TTL = 30  # 30 minutes
_USER_TOKEN_REFRESH_TTL = 2  # 2 days


async def is_valid_token(redis_client: aioredis.StrictRedis, token: str):
    if await redis_client.get(token):
        return True
    else:
        return False


async def generate_token(redis_client: aioredis.StrictRedis, user_id: int):
    access_token = jwt.encode(
        payload={
            'user_id': user_id,
            'iss': config.HOST_NAME,
            'exp': (datetime.now(TZ_UTC) + timedelta(hours=_USER_LOGIN_TTL)).timestamp(),
        },
        key=config.SECRET_KEY,
        algorithm='HS256',
    )

    refresh_token = jwt.encode(
        payload={
            'user_id': user_id,
            'iss': config.HOST_NAME,
            'exp': (datetime.now(TZ_UTC) + timedelta(days=_USER_TOKEN_REFRESH_TTL)).timestamp(),
        },
        key=config.SECRET_KEY,
        algorithm='HS256',
    )

    # Redis 에 생성된 token 추가
    await redis_client.set(access_token, refresh_token)
    return access_token, refresh_token


def is_expired_token(token):
    decoded_token = jwt.decode(token, config.SECRET_KEY, algorithms='HS256')
    if decoded_token.get("exp") is None or decoded_token.get("exp") < datetime.now(TZ_UTC).timestamp():
        return True
    else:
        return False
