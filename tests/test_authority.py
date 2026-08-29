from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[1]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def test_authority_files_are_exact_uploaded_inputs():
    assert sha(ROOT/"plan.md")=="2e713f1d1b72b1c58bc532de261a86ca00834aecd84645a95f9624e57bba766d"
    assert sha(ROOT/"bronze-age-simulation-encyclopedia.md")=="a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937"
