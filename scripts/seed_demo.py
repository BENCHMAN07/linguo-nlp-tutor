"""Seed a clearly labeled teacher-demo class using real sourced question IDs."""
import json
import sys
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.main import Attempt, Player, engine
questions=json.loads((ROOT/"data/questions.json").read_text(encoding="utf-8"))
if not questions:
    print("No demo attempts seeded: the course question bank is empty.")
    raise SystemExit(0)
with Session(engine) as db:
    existing=db.scalars(select(Player).where(Player.name.like("Demo %"))).all()
    if existing:
        print(f"Demo class already has {len(existing)} learners; leaving it unchanged.")
    else:
        for index,name in enumerate(("Demo Asha","Demo Ravi","Demo Mei")):
            p=Player(name=name,class_name="Computational Linguistics · Demo")
            db.add(p);db.flush()
            chosen=questions[index*10:(index+1)*10]
            for offset,q in enumerate(chosen):
                correct=(offset+index)%4!=0
                db.add(Attempt(player_id=p.id,question_id=q["id"],topic=q["topic"],answer=q["answer"] if correct else "demo response",correct=correct,score=float(correct),response_time_ms=5500+offset*700,hint_count=0))
            p.xp=sum(10 if (offset+index)%4 else 1 for offset in range(len(chosen)))
        db.commit()
        print("Seeded a three learner demo class with attempts tied to the scraped question bank.")
