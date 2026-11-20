"""Download optional NLP corpora/models during initial setup, never at app runtime."""
import nltk

for resource in ("punkt", "averaged_perceptron_tagger", "wordnet"):
    nltk.download(resource, quiet=True)

try:
    import spacy
    try:
        spacy.load("en_core_web_sm")
    except OSError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
except ImportError:
    print("spaCy is unavailable in this Python build; POS/NER show an explicit model-unavailable result.")
