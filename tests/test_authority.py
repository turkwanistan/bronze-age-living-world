from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[1]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def test_authority_files_match_current_project_authority():
    assert sha(ROOT/"plan.md")=="f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d"
    assert sha(ROOT/"bronze-age-simulation-encyclopedia.md")=="a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937"
