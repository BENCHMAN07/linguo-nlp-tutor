from backend.nlp.tools import tokenize, pos_tag, entities, stems_lemmas, similarity, cfg_parse

def test_tokenization_splits_words_and_sentences():
    result=tokenize("Hello, linguists. Study NLP!")
    assert result["words"]==["Hello",",","linguists",".","Study","NLP","!"]
    assert len(result["sentences"])==2

def test_pos_and_ner_return_explicit_outputs():
    assert pos_tag("A parser works.")
    assert isinstance(entities("Ada Lovelace visited London on Monday."),list)

def test_stemming_similarity_and_cfg():
    assert stems_lemmas("studies")[0]["porter"]!="studies"
    assert similarity("cats chase mice","cats chase mice")["cosine_tfidf"]>.99
    assert cfg_parse("the linguist studies language")["matched"]
