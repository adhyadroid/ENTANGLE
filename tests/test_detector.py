"""tests/test_detector.py"""
from detector import SPRT, calibrate_baseline, hoeffding_false_accept_bound


def test_sprt_accepts_low_mismatch_stream():
    s = SPRT(p0=0.02, p1=0.17, alpha=0.01, beta=0.01)
    decision = "continue"
    for i in range(300):
        r = s.update(mismatch=(i % 50 == 0))  # ~2% mismatch, matches p0
        decision = r.decision
        if decision != "continue":
            break
    assert decision == "accept"


def test_sprt_rejects_high_mismatch_stream():
    s = SPRT(p0=0.02, p1=0.17, alpha=0.01, beta=0.01)
    decision = "continue"
    for i in range(300):
        r = s.update(mismatch=(i % 3 == 0))  # ~33% mismatch, well above p1
        decision = r.decision
        if decision != "continue":
            break
    assert decision == "reject"


def test_calibrate_baseline_floor():
    assert calibrate_baseline([]) > 0  # never returns 0 (avoids log(0) in SPRT)
    assert calibrate_baseline([False] * 100) > 0


def test_hoeffding_bound_shrinks_with_more_rounds():
    b1 = hoeffding_false_accept_bound(n=50, epsilon=0.075)
    b2 = hoeffding_false_accept_bound(n=500, epsilon=0.075)
    assert b2 < b1
