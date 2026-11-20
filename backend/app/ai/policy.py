from collections import defaultdict,deque
import time

class PolicyError(Exception):pass
class UsagePolicy:
    def __init__(self,per_minute:int=10):self.per_minute=per_minute;self.calls=defaultdict(deque)
    def check(self,user:str,daily_used:int,daily_budget:int,now:float|None=None):
        now=time.monotonic() if now is None else now
        q=self.calls[user]
        while q and now-q[0]>=60:q.popleft()
        if len(q)>=self.per_minute:raise PolicyError("rate_limit")
        if daily_used>=daily_budget:raise PolicyError("daily_budget")
        q.append(now)
