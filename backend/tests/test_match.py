from app.services.match import compute_match

REPOS = [{"language": "Python", "is_fork": 0}, {"language": "Python", "is_fork": 0},
         {"language": "JavaScript", "is_fork": 0}]


def test_full_match():
    r = compute_match("We need Python and JavaScript engineers", REPOS)
    assert r["percentage"] >= 70 and r["missing"] == []


def test_gap_reported():
    r = compute_match("Rust and Python required", REPOS)
    assert "Rust" in r["missing"]


def test_empty_jd():
    import pytest
    with pytest.raises(ValueError):
        compute_match("   ", REPOS)