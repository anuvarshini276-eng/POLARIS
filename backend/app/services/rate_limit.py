"""Redis-backed fixed windows in deployed mode, bounded local windows for a single process."""
import os,time
from collections import defaultdict,deque
from fastapi import HTTPException
local=defaultdict(deque)
redis_client=None
if os.getenv('REDIS_URL'):
    from redis import Redis
    redis_client=Redis.from_url(os.environ['REDIS_URL'],socket_connect_timeout=2,socket_timeout=2)
def allowed(host,auth):
    limit=30 if auth else 600
    if redis_client:
        try:
            key=f'polaris:rate:{host}:{int(auth)}:{int(time.time()//60)}'
            count=redis_client.incr(key)
            if count==1: redis_client.expire(key,65)
            return count<=limit
        except Exception:
            # Fail closed on authentication rather than silently dropping the configured shared limiter.
            if auth: return False
    now=time.time();key=(host,auth);queue=local[key]
    while queue and queue[0]<now-60: queue.popleft()
    if len(queue)>=limit:return False
    queue.append(now)
    if len(local)>10000:
        for old in list(local):
            if not local[old] or local[old][-1]<now-120: del local[old]
    return True
