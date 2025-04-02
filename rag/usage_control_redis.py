import redis
from datetime import datetime

# Redis 연결
r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

def check_usage_limit_redis(user_id: int, max_per_day: int = 20) -> bool:
    today = datetime.now().date().isoformat()
    key = f"usage:{user_id}:{today}"

    current = r.get(key)
    if current is not None and int(current) >= max_per_day:
        return False

    # incr()은 키가 없으면 1로 만들고, 있으면 +1 해줌
    new_count = r.incr(key)

    # 키가 새로 만들어졌다면 TTL 설정 (24시간)
    if new_count == 1:
        r.expire(key, 86400)

    return True
