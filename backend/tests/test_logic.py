from types import SimpleNamespace
from datetime import datetime, timezone
from backend.app.logic import xp_award, recency_weighted_accuracy, streak_after, weak_topic, update_elo, adapt_questions

def test_xp_first_try_hint_repeat_speed_and_farming_caps():
    assert xp_award(True,0,9000,0,0)==(10,0)
    assert xp_award(True,1,9000,0,0)==(5,0)
    assert xp_award(False,0,9000,0,0)==(1,0)
    assert xp_award(True,0,1000,0,15)==(15,5)
    assert xp_award(True,0,1000,4,20,4)==(0,0)

def test_mastery_weights_recent_answers_more():
    now=datetime.now(timezone.utc)
    rows=[SimpleNamespace(ts=now,score=0),SimpleNamespace(ts=now,score=1)]
    assert recency_weighted_accuracy(rows)<.5
    assert recency_weighted_accuracy([])==0

def test_streak_and_weakness_threshold():
    assert streak_after(4,"2026-10-27","2026-10-28","2026-10-27")==5
    assert streak_after(4,"2026-10-20","2026-10-28","2026-10-27")==1
    assert weak_topic([0,0,1,0,0])
    assert not weak_topic([0,0,1,0])

def test_five_wrong_answers_trigger_training_camp():
    recent_answers=[]
    for _ in range(5):recent_answers.append(0.0)
    assert weak_topic(recent_answers)

def test_elo_changes_the_question_served_after_performance_streak():
    rows=[{"id":"easy"},{"id":"mid"},{"id":"hard"}]
    ratings={"easy":600,"mid":800,"hard":1000}
    before=adapt_questions(rows,1000,ratings)[0]["id"]
    player,question=1000,1000
    for _ in range(12):player,question=update_elo(player,question,True)
    after=adapt_questions(rows,player,ratings)[0]["id"]
    assert before=="mid"
    assert after=="hard"
