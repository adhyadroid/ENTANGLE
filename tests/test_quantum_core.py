"""tests/test_quantum_core.py — Phase 1 requirement: teleportation tested independently first."""
import random
from quantum_core import run_round


def test_honest_teleportation_exact_reconstruction():
    """First success condition (Section 3): undisturbed teleportation must
    reconstruct the exact intended bit, in matching basis, every time."""
    random.seed(0)
    mismatches = 0
    n = 200
    for _ in range(n):
        bit = random.choice([0, 1])
        basis = random.choice(["Z", "X"])
        out = run_round(bit, basis, basis)
        if out != bit:
            mismatches += 1
    assert mismatches == 0


def test_wrong_basis_measurement_is_random():
    """Measuring in the wrong Pauli basis must give ~50% mismatch — proof
    this is real quantum randomness, not a classical copy of the bit."""
    random.seed(1)
    n = 300
    mismatches = sum(1 for _ in range(n) if run_round(random.choice([0, 1]), "Z", "X") != random.choice([0, 1]))
    # re-run properly paired
    random.seed(1)
    mismatches = 0
    for _ in range(n):
        bit = random.choice([0, 1])
        out = run_round(bit, "Z", "X")
        if out != bit:
            mismatches += 1
    rate = mismatches / n
    assert 0.35 < rate < 0.65


def test_intercept_resend_produces_elevated_mismatch():
    random.seed(2)
    n = 300
    mismatches = 0
    for _ in range(n):
        bit = random.choice([0, 1])
        basis = random.choice(["Z", "X"])
        out = run_round(bit, basis, basis, eve_intercept=True, eve_basis=random.choice(["Z", "X"]))
        if out != bit:
            mismatches += 1
    rate = mismatches / n
    assert 0.15 < rate < 0.35  # textbook ~0.25


def test_impersonation_uncorrelated_with_token():
    random.seed(3)
    n = 300
    mismatches = 0
    for _ in range(n):
        bit = random.choice([0, 1])
        basis = random.choice(["Z", "X"])
        out = run_round(bit, basis, basis, no_entanglement=True)
        if out != bit:
            mismatches += 1
    rate = mismatches / n
    assert 0.35 < rate < 0.65
