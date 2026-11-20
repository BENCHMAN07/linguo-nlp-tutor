from backend.tutor.retrieval import retrieve

def passages(query:str,limit:int=3):
    hits=retrieve(query[:1200],limit)
    return [{"title":h["title"],"heading":h["heading"],"text":h["text"][:2200],"url":h["url"],"score":h["score"]} for h in hits]
def context_block(hits:list[dict])->str:
    return "\n\n".join(f"Lecture: {h['title']} — {h['heading']}\nURL: {h['url']}\nPassage:\n{h['text']}" for h in hits)
def valid_citations(citations:list,grounded:list[dict])->bool:
    allowed={h["url"] for h in grounded}
    return bool(citations) and all(c.url in allowed for c in citations)
