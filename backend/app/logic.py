from __future__ import annotations
from datetime import datetime

def xp_award(correct:bool,hint_count:int,response_time_ms:int,repeated_count:int,speed_xp_today:int,replay_number:int=1)->tuple[int,int]:
    """Return total XP and speed component after daily/replay farming caps."""
    if replay_number>3:return 0,0
    base=5 if correct and hint_count else 10 if correct else 1
    speed=min(5,max(0,20-speed_xp_today)) if correct and response_time_ms<5000 else 0
    total=max(1,base+speed-max(0,repeated_count-2)*2)
    speed=min(speed,total) if correct else 0
    return total,speed

def recency_weighted_accuracy(attempts:list)->float:
    if not attempts:return 0.0
    ordered=sorted(attempts,key=lambda a:a.ts,reverse=True)
    weights=[.85**i for i in range(len(ordered))]
    return sum(float(a.score)*w for a,w in zip(ordered,weights))/sum(weights)

def streak_after(prior:int,last_active:str,today:str,yesterday:str)->int:
    if last_active==today:return prior
    if last_active==yesterday:return prior+1
    return 1

def weak_topic(scores:list[float],threshold:float=.60,window:int=5)->bool:
    return len(scores)>=window and sum(scores[-window:])/window<threshold

def update_elo(player_rating:float,question_rating:float,correct:bool,k:float=32)->tuple[float,float]:
    expected=1/(1+10**((question_rating-player_rating)/400))
    delta=k*((1.0 if correct else 0.0)-expected)
    return player_rating+delta,question_rating-delta

def flow_target_rating(player_rating:float,success_probability:float=.75)->float:
    return player_rating+400*__import__('math').log10(1/success_probability-1)

def adapt_questions(rows:list[dict],player_rating:float,question_ratings:dict[str,float])->list[dict]:
    target=flow_target_rating(player_rating)
    return sorted(rows,key=lambda q:abs(question_ratings.get(q["id"],float(q.get("rating",1000)))-target))
