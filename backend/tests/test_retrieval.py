from backend.tutor.retrieval import retrieve

def test_retrieval_returns_grounded_passage_and_source():
    hits=retrieve("context free grammar")
    assert hits
    assert hits[0]["text"]
    assert hits[0]["url"].startswith("https://lectures.rebeccakennet.com/")

def test_retrieval_does_not_invent_for_empty_query():
    assert retrieve("")==[]
