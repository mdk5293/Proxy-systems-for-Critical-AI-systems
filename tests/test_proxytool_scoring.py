from proxytool_redux.scoring import contrastive_adjust, rank_fraction, winsor_bounds


def test_contrastive_adjust_no_negs():
    assert contrastive_adjust(0.7, [], temperature=6.0) == 0.7


def test_contrastive_adjust_symmetric():
    # median negatives = 0.5, raw 0.5 -> delta 0 -> sigmoid 0.5
    assert abs(contrastive_adjust(0.5, [0.4, 0.5, 0.6], temperature=6.0) - 0.5) < 1e-9


def test_contrastive_adjust_favors_raw_above_median():
    s = contrastive_adjust(0.9, [0.1, 0.2, 0.3], temperature=6.0)
    assert s > 0.5


def test_rank_fraction_endpoints():
    urls = ["a", "b", "c"]
    assert rank_fraction(urls, "a") == 1.0
    assert rank_fraction(urls, "c") == 0.0
    assert abs(rank_fraction(urls, "b") - 0.5) < 1e-9


def test_winsor_bounds():
    lo, hi = winsor_bounds([1.0, 2.0, 3.0, 100.0], q_low=0.25, q_high=0.75)
    assert lo <= hi
