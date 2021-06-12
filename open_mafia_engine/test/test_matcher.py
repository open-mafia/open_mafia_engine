from open_mafia_engine.util.matcher import FuzzyMatcher


def test_fuzzy():
    """Tests fuzzy matching at different levels.

    TODO: Make test more comprehensive. Maybe use real-world cases?
    """

    matcher = FuzzyMatcher[str]({"abacus": "a", "peter": "p"}, score_cutoff=0)
    assert matcher["poodle"] == "p"
