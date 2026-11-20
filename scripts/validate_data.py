import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
expected={1:6,2:8,3:8,4:9,5:7}
lectures=json.loads((ROOT/"data/lectures.json").read_text(encoding="utf-8"))
questions=json.loads((ROOT/"data/questions.json").read_text(encoding="utf-8"))
exam=json.loads((ROOT/"data/exam_prep.json").read_text(encoding="utf-8"))
counts=Counter(l.get("unit") for l in lectures)
assert all(counts[u]==n for u,n in expected.items()),f"Lecture count gap: {dict(counts)}"
assert all(l.get("sections") for l in lectures),"A lecture has no extracted content"
urls={l["url"] for l in lectures}
assert len(questions)>=40,"Question bank needs at least eight items per unit"
assert all(sum(q.get("unit")==u for q in questions)>=8 for u in expected),"Question count gap by unit"
for q in questions:
    if q.get("grading")=="ungraded_source_prompt":
        assert q.get("source_lecture",{}).get("url").endswith("/exam-prep/"),f"Uncited exam prompt: {q.get('id')}"
        exam_text=" ".join(section.get("text","") for section in exam.get("sections",[]))
        assert q["question"] in exam_text,f"Exam prompt not present in source: {q.get('id')}"
        continue
    assert q.get("source_lecture",{}).get("url") in urls,f"Uncited question: {q.get('id')}"
    if q.get("type")=="multiple_choice":
        assert q.get("answer") in q.get("options",[]),f"Missing correct option: {q.get('id')}"
    source=next(l for l in lectures if l["url"]==q["source_lecture"]["url"])
    body=" ".join(section.get("text","") for section in source.get("sections",[])).casefold()
    assert q.get("answer","").casefold() in body,f"Answer not found in source lecture: {q.get('id')}"
    assert all(option.casefold()==q["answer"].casefold() or option.casefold() not in body for option in q.get("options",[])),f"Distractor appears in source: {q.get('id')}"
print(json.dumps({"lectures":len(lectures),"lectures_per_unit":dict(counts),"questions":len(questions),"auto_graded":sum(q.get('grading','auto')=='auto' for q in questions),"exam_prep_prompts":sum(q.get('grading')=='ungraded_source_prompt' for q in questions),"questions_per_unit":dict(Counter(q['unit'] for q in questions))},indent=2))
