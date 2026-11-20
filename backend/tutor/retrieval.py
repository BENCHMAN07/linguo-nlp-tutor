from pathlib import Path
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA=Path(__file__).resolve().parents[2]/"data"
def retrieve(query:str,limit:int=3):
    try:lectures=json.loads((DATA/"lectures.json").read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError):lectures=[]
    chunks=[]
    for lecture in lectures:
        for section in lecture.get("sections",[]):
            text=section.get("text","").strip()
            if text:chunks.append({"text":text,"heading":section.get("heading",""),"title":lecture.get("title",""),"unit":lecture.get("unit"),"url":lecture.get("url","")})
    if not query.strip() or not chunks:return []
    try:
        matrix=TfidfVectorizer(stop_words="english").fit_transform([c["text"] for c in chunks]+[query])
        scores=cosine_similarity(matrix[-1],matrix[:-1]).ravel()
    except ValueError:return []
    indices=scores.argsort()[::-1][:limit]
    return [{**chunks[i],"score":float(scores[i])} for i in indices if scores[i]>=.04]
