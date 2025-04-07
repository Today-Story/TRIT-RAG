import redis
from datetime import datetime

r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

def get_usage_key(user_id: int, needs: str):
    today = datetime.now().date().isoformat()
    return f"usage:{user_id}:{today}:{needs}"

def get_remaining_usage(user_id: int, needs: str, max_per_day: int = 20) -> int:
    key = get_usage_key(user_id, needs)
    current = r.get(key)
    return max_per_day - int(current or 0)

def is_under_limit(user_id: int, needs: str, max_per_day: int = 20) -> bool:
    return get_remaining_usage(user_id, needs, max_per_day) > 0

def increment_usage(user_id: int, needs: str):
    key = get_usage_key(user_id, needs)
    new_count = r.incr(key)
    if new_count == 1:
        r.expire(key, 86400)
