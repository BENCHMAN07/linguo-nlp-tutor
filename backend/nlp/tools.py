from __future__ import annotations
import re
from functools import lru_cache

TOKEN_RE=re.compile(r"\w+(?:['’]\w+)*|[^\w\s]",re.UNICODE)
@lru_cache(maxsize=1)
def _spacy_model():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except (ImportError,OSError):return None
def has_spacy_model()->bool:return _spacy_model() is not None
def tokenize(text:str):
    words=TOKEN_RE.findall(text)
    sentences=[x for x in re.split(r"(?<=[.!?])\s+",text.strip()) if x]
    subwords=[]
    for word in words:
        if re.fullmatch(r"\w+",word) and len(word)>6:subwords.extend((word[:3],"##"+word[3:]))
        else:subwords.append(word)
    return {"words":words,"sentences":sentences,"subwords":subwords}
def pos_tag(text:str):
    nlp=_spacy_model()
    if nlp:return [{"text":t.text,"tag":t.pos_,"label":t.tag_} for t in nlp(text)]
    return [{"text":t,"tag":"PUNCT" if re.fullmatch(r"\W+",t) else "UNKNOWN","label":"rule/model unavailable"} for t in TOKEN_RE.findall(text)]
def entities(text:str):
    nlp=_spacy_model()
    if not nlp:return []
    doc=nlp(text);names={"ORG":"ORGANIZATION","GPE":"LOCATION","LOC":"LOCATION"}
    return [{"text":e.text,"label":names.get(e.label_,e.label_)} for e in doc.ents if e.label_ in {"PERSON","ORG","GPE","LOC","DATE"}]
def stems_lemmas(text:str):
    from nltk.stem import PorterStemmer, SnowballStemmer
    words=[x for x in TOKEN_RE.findall(text) if x.isalpha()]
    p,s=PorterStemmer(),SnowballStemmer("english")
    nlp=_spacy_model()
    lemmas={t.text.lower():t.lemma_ for t in nlp(" ".join(words))} if nlp else {w.lower():w.lower() for w in words}
    return [{"word":w,"porter":p.stem(w.lower()),"snowball":s.stem(w.lower()),"lemma":lemmas.get(w.lower(),w.lower())} for w in words]
def similarity(a:str,b:str):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    try:cos=float(cosine_similarity(TfidfVectorizer().fit_transform([a,b]))[0,1])
    except ValueError:cos=0.0
    ta=set(re.findall(r"\w+",a.lower()));tb=set(re.findall(r"\w+",b.lower()))
    return {"cosine_tfidf":cos,"jaccard":len(ta&tb)/len(ta|tb) if ta|tb else 0.0}
def cfg_parse(sentence:str):
    try:
        from nltk import CFG, ChartParser
        grammar=CFG.fromstring("""S -> NP VP\nNP -> Det N | Det Adj N | N\nVP -> V NP | V\nDet -> 'the' | 'a' | 'an'\nAdj -> 'small' | 'curious'\nN -> 'linguist' | 'student' | 'cat' | 'language'\nV -> 'studies' | 'sees' | 'runs'""")
        tokens=[w.lower() for w in TOKEN_RE.findall(sentence) if w.isalpha()]
        trees=list(ChartParser(grammar).parse(tokens))
        return {"tokens":tokens,"trees":[str(t) for t in trees[:3]],"matched":bool(trees)}
    except (ImportError,ValueError):return {"tokens":TOKEN_RE.findall(sentence),"trees":[],"matched":False}
