"""tests/test_protocol.py"""
import random
from detector import SPRT
from protocol import run_protocol_round


def test_bob_and_charlie_are_independent_streams():
    """Charlie must not merely copy Bob's result (Section 5 requirement).
    Under 'clean' mode, teleportation is deterministic, so both verifiers
    correctly reconstruct the same intended bit every round — that's not
    evidence of dependence, it's the correct physics (see
    test_quantum_core.test_honest_teleportation_exact_reconstruction).
    Independence has to be checked under a mode with real per-verifier
    randomness: intercept_resend disturbs each verifier's qubit via a
    separately, randomly chosen Eve measurement basis per circuit call."""
    rng = random.Random(0)
    bob_sprt, charlie_sprt = SPRT(0.02, 0.17), SPRT(0.02, 0.17)
    bob_mismatches, charlie_mismatches = [], []
    for i in range(60):
        rec = run_protocol_round(i, "intercept_resend", bob_sprt, charlie_sprt, rng=rng)
        bob_mismatches.append(rec.bob_mismatch)
        charlie_mismatches.append(rec.charlie_mismatch)
    # If Charlie were just copying Bob, these two mismatch sequences would
    # be identical; independent circuit executions should disagree on some
    # rounds (Eve's basis choice is drawn separately for each verifier).
    assert bob_mismatches != charlie_mismatches


def test_symmetrization_requires_both_accept():
    rng = random.Random(1)
    bob_sprt, charlie_sprt = SPRT(0.02, 0.17), SPRT(0.02, 0.17)
    final = "continue"
    for i in range(300):
        rec = run_protocol_round(i, "clean", bob_sprt, charlie_sprt, rng=rng)
        if rec.symmetrized_decision != "continue":
            final = rec.symmetrized_decision
            break
    assert final == "accept"


def test_intercept_resend_reaches_reject_via_symmetrization():
    rng = random.Random(2)
    bob_sprt, charlie_sprt = SPRT(0.02, 0.17), SPRT(0.02, 0.17)
    final = "continue"
    for i in range(300):
        rec = run_protocol_round(i, "intercept_resend", bob_sprt, charlie_sprt, rng=rng)
        if rec.symmetrized_decision != "continue":
            final = rec.symmetrized_decision
            break
    assert final == "reject"
