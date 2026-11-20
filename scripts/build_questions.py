"""Build a conservative question bank from terms and text present in scraped lectures."""
import json
import random
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
lectures=json.loads((ROOT/"data"/"lectures.json").read_text(encoding="utf-8"))
questions=[]
seen=set()
skip={"about","after","also","aspect","being","between","could","core","define","depends","describe","discuss","distinguish","each","explain","figure","first","from","general","have","here","identify","illustrate","important","into","language","linguistic","natural","other","possible","provide","related","their","there","these","those","through","under","using","various","which","while","where","would","with"}
term_sources=[]
for lecture in lectures:
    body=" ".join(section.get("text","") for section in lecture.get("sections",[]))
    term_sources.extend((term,body,lecture) for term in lecture.get("key_terms",[]) if len(term)>=5 and term.casefold() not in skip)
for lecture in lectures:
    unit=lecture.get("unit",0)
    terms=[t for t in lecture.get("key_terms",[]) if len(t)>=5 and t.casefold() not in skip and t.casefold() not in seen]
    # Keep a compact question set per lecture; each correct answer occurs verbatim
    # in the corresponding source passage, and every item links back to it.
    for term in terms[:10]:
        normalized=term.strip()
        if not normalized or normalized.casefold() in seen: continue
        seen.add(normalized.casefold())
        excerpt=next((s.get("text","") for s in lecture.get("sections",[]) if normalized.casefold() in s.get("text","").casefold()),"")
        if not excerpt: continue
        qid=f"u{unit}-{len(questions)+1}"
        source_text=" ".join(s.get("text","") for s in lecture.get("sections",[]))
        distractors=[]
        for candidate,candidate_text,candidate_lecture in term_sources:
            if candidate.casefold()==normalized.casefold() or candidate.casefold() in source_text.casefold() or candidate.casefold() in {x.casefold() for x in distractors}:continue
            if candidate_lecture.get("unit")==unit:
                distractors.append(candidate)
            if len(distractors)==3:break
        options=[normalized]+distractors
        random.Random(qid).shuffle(options)
        questions.append({"id":qid,"topic":lecture.get("title",""),"unit":unit,"difficulty":"introductory","type":"multiple_choice" if len(options)==4 else "short_answer",
            "question":f"Which term appears in the lecture ‘{lecture.get('title','')}’?",
            "options":options if len(options)==4 else [],"answer":normalized,"explanation":f"‘{normalized}’ appears in this lecture. Review the cited passage for its context.",
            "rating":800+min(600,len(normalized)*28),"source_lecture":{"title":lecture.get("title"),"url":lecture.get("url")}})
# Exam-prep page items are copied verbatim as discussion prompts. That page has
# no answer key, so these are explicitly ungraded and never enter auto-graded levels.
exam=json.loads((ROOT/"data"/"exam_prep.json").read_text(encoding="utf-8"))
sections=exam.get("sections",[])
topic_lines=[line.strip().lstrip("•\ufffd-–— ").strip() for line in (sections[1].get("text","").splitlines() if len(sections)>1 else []) if line.strip()]
def norm(value):return re.sub(r"[^a-z0-9]+","",value.casefold().replace("\ufffd",""))
def unit_for_topic(name):
    target=norm(name)
    for lecture in lectures:
        title=norm(re.sub(r"\s*[·–-]\s*21CSE552T.*$","",lecture.get("title","")))
        if target and (target==title or target in title or title in target):return lecture["unit"],lecture.get("title",name)
    return 0,name
for index,section in enumerate(sections[2:]):
    topic_index=index//3
    if topic_index>=len(topic_lines):break
    unit,title=unit_for_topic(topic_lines[topic_index])
    if not unit:continue
    mark=section.get("heading","").split()[0]
    for prompt in section.get("text","").splitlines():
        prompt=prompt.strip().lstrip("•\ufffd-–— ").strip()
        if not prompt:continue
        questions.append({"id":f"exam-u{unit}-{len(questions)+1}","topic":title,"unit":unit,
            "difficulty":mark.lower(),"type":"reflection","grading":"ungraded_source_prompt",
            "question":prompt,"options":[],"exam_mark":mark,
            "explanation":"Exam-prep prompt copied from the course page. The source provides no answer key, so Linguo does not auto-grade it.",
            "source_lecture":{"title":"Exam preparation · "+title,"url":"https://lectures.rebeccakennet.com/21cse552t-computational-linguistics/exam-prep/"}})
(ROOT/"data"/"questions.json").write_text(json.dumps(questions,indent=2,ensure_ascii=False),encoding="utf-8")
counts={str(u):sum(q["unit"]==u for q in questions) for u in range(1,6)}
print(json.dumps({"question_count":len(questions),"auto_graded":sum(q.get("grading","auto")=="auto" for q in questions),
                  "exam_prep_prompts":sum(q.get("grading")=="ungraded_source_prompt" for q in questions),"per_unit":counts,
                  "validation":"auto-graded answers come from lecture text; exam prompts are copied verbatim without invented answers"},indent=2))
