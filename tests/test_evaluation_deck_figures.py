"""Validate and exercise the aggregate-only presentation figure profile."""

from hashlib import sha256
import json
from math import isnan

import pytest

pytest.importorskip("matplotlib")

from tools import render_evaluation_figures as deck


def sample():
    return {
        "input_class": "synthetic_only", "period_months": 3,
        "activity": [
            {"month": "2034-01", "admissions": 40, "icu1_pct": 77, "icu2_pct": 78},
            {"month": "2034-02", "admissions": 39, "icu1_pct": None, "icu2_pct": 80},
            {"month": "2034-03", "admissions": 54, "icu1_pct": 74, "icu2_pct": 81},
        ],
        "pathways": {
            "screen_months": 2, "adult_icu_destinations": 53, "labelled": 20, "chart_review": 12,
            "avoided": 3.2, "reused_hours": 138, "added": 1.8,
        },
        "funding": {
            key: {"full_net_payment": 100_000 + 10_000 * i, "incremental_spending": 85_000 + 17_000 * i}
            for i, key in enumerate(deck.SCENARIOS)
        },
    }


def test_contract_renders_registered_figures(tmp_path):
    data = sample()
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps(data))
    destination = tmp_path / "figures"
    result = deck.build(inputs, destination)
    spec = json.loads(deck.CONTRACT.read_text())
    catalogue = json.loads((deck.CONTRACT.parent / "catalogue.json").read_text())
    assert [item["id"] for item in result["figures"]] == [item["id"] for item in spec["figures"]]
    for profile in [*spec["figures"], spec["companion"]]:
        assert set(profile["related_catalogue_ids"]) <= {item["id"] for item in catalogue["figures"]}
    for i, item in enumerate(result["figures"]):
        stem = spec["figures"][i]["artifact_stem"]
        assert set(item["files"]) == {f"{stem}.svg", f"{stem}.png"}
        assert "FICTIONAL" in (destination / f"{stem}.svg").read_text()
        for name, digest in item["files"].items():
            assert sha256((destination / name).read_bytes()).hexdigest() == digest
    with pytest.raises(FileExistsError):
        deck.build(inputs, destination)


def test_numeric_marks_preserve_missingness_and_cash_sign():
    figures = [
        deck.activity(sample(), {}),
        deck.funding(sample(), {"payment_range_percent": [75, 100]}),
    ]
    try:
        assert isnan(figures[0].axes[1].lines[0].get_ydata()[1])
        assert list(figures[1].axes[0].lines[0].get_xdata()) == [75, 100]
        assert list(figures[1].axes[0].lines[0].get_ydata()) == [-10.0, 15.0]
    finally:
        for fig in figures:
            deck.plt.close(fig)


def test_invalid_screening_rejected():
    data = sample()
    data["pathways"]["chart_review"] = 22
    with pytest.raises(ValueError, match="counts do not reconcile"):
        deck.validate(data)


def test_private_input_rejected_in_git_worktree(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").write_text("gitdir: fixture")
    data = sample()
    data["input_class"] = "private_aggregate"
    file = project / "aggregates.json"
    file.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="outside Git worktrees"):
        deck.build(file, tmp_path / "figures")
