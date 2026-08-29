from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_v017_fresh_cognition_pairs_rebuild_and_validate(tmp_path: Path):
    source = ROOT / "state" / "ugarit_living_v015.sqlite"
    property_source = ROOT / "state" / "ugarit_living_v014.sqlite"
    decisions = ROOT / "runs" / "VALIDATION_V017_FRESH_PAIR_DECISIONS.json"
    if not source.exists() or not property_source.exists():
        pytest.skip("accepted v014/v015 DB unavailable")

    scratch = Path(tempfile.mkdtemp(prefix=".v017-pair-test-", dir=ROOT))
    workdir = scratch / "pairs"
    packets = scratch / "packets.json"
    results = scratch / "results.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_fresh_cognition_pairs.py"),
            "--source-db", str(source),
            "--property-source-db", str(property_source),
            "--root", str(ROOT),
            "--workdir", str(workdir),
            "--json-out", str(packets),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "apply_fresh_cognition_pairs.py"),
            "--packets", str(packets),
            "--decisions", str(decisions),
            "--json-out", str(results),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    packet_data = json.loads(packets.read_text())
    result_data = json.loads(results.read_text())
    assert len(packet_data) == 10
    assert result_data["mode"] == "fresh_cognition_paired_validation"
    assert result_data["all_checks_pass"] is True
    assert all(result_data["pair_checks"].values())
    assert all(r["ok"] for r in result_data["results"].values())
    assert all(r["rejected_jobs"] == 0 for r in result_data["results"].values())
    assert all(r["negative_resources"] == 0 for r in result_data["results"].values())
    import shutil
    shutil.rmtree(scratch, ignore_errors=True)


def test_v017_frozen_artifacts_are_complete_and_fresh_labeled():
    packets = json.loads((ROOT / "runs" / "VALIDATION_V017_FRESH_PAIR_PACKETS.json").read_text())
    decisions = json.loads((ROOT / "runs" / "VALIDATION_V017_FRESH_PAIR_DECISIONS.json").read_text())
    results = json.loads((ROOT / "runs" / "VALIDATION_V017_FRESH_PAIR_RESULTS.json").read_text())

    expected = {
        "p10_illness_adequate", "p10_illness_depleted",
        "p7_recycling_buffered", "p7_recycling_near_exhausted",
        "p16_care_no_conflict", "p16_care_recovery_conflict",
        "p16_stewardship_funded", "p16_stewardship_underfunded",
        "p3_shipping_single_report", "p3_shipping_discordant_reports",
    }
    assert set(packets) == expected
    assert set(decisions) == expected
    assert set(results["results"]) == expected
    assert results["all_checks_pass"] is True
    assert all(v.get("declared_uncertainty") for v in decisions.values())
    assert all(v.get("decision_basis_tags") for v in decisions.values())
