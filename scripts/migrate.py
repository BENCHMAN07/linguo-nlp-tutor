"""Idempotently create or upgrade the local SQLite schema."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.main import Base, engine
Base.metadata.create_all(engine)
print("Linguo SQLite schema is current.")
