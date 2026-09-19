"""tests/test_phase2.py — diagnostic additions; none of these gate accept/reject."""
import random
import dataclasses

from quantum_core import chsh_s_value, approximate_cloning_round, run_round
from classical_channel import ClassicalChannel, WegmanCarterMAC
from detector import chi_square_check


def test_chsh_honest_exceeds_classical_bound():
    s = chsh_s_value(eve_intercept=False, shots=1000)
    assert s > 2.0  # violates the classical (local-hidden-variable) bound
    assert s <= 2.9  # within numerical slack of Tsirelson's bound 2.828


def test_chsh_degrades_under_interception():
    s_honest = chsh_s_value(eve_intercept=False, shots=1000)
    s_attacked = chsh_s_value(eve_intercept=True, shots=1000)
    assert s_attacked < s_honest


def test_cloning_attack_mismatch_between_noise_and_intercept_resend():
    random.seed(0)
    n = 300
    cloning_mism = 0
    ir_mism = 0
    for _ in range(n):
        bit = random.choice([0, 1])
        basis = random.choice(["Z", "X"])
        if approximate_cloning_round(bit, basis, basis) != bit:
            cloning_mism += 1
    random.seed(0)
    for _ in range(n):
        bit = random.choice([0, 1])
        basis = random.choice(["Z", "X"])
        if run_round(bit, basis, basis, eve_intercept=True, eve_basis=random.choice(["Z", "X"])) != bit:
            ir_mism += 1
    # cloning's weaker (partial) disturbance should mismatch less often than
    # intercept-resend's full projective measurement + resend
    assert 0 < cloning_mism < ir_mism


def test_mac_detects_tamper_but_not_confused_with_replay():
    ch = ClassicalChannel()
    mac = WegmanCarterMAC(random.Random(0))
    t = ch.send(round_id=1, bits=(1, 0), basis="Z", nonce="n1")
    tag = mac.tag_for(t)
    assert mac.verify(t, tag) is True
    tampered = dataclasses.replace(t, classical_bits=(0, 0))
    assert mac.verify(tampered, tag) is False  # tamper caught
    # replay defense is a separate mechanism entirely, unaffected by the MAC:
    assert ch.receive(t) is True
    assert ch.receive(t) is False


def test_chi_square_agrees_with_honest_low_mismatch():
    mismatches = [False] * 98 + [True] * 2  # ~2% mismatch rate
    result = chi_square_check(mismatches, p0=0.02)
    assert result["verdict"] == "accept"


def test_chi_square_flags_elevated_mismatch():
    mismatches = [False] * 70 + [True] * 30  # 30% mismatch, well above p0
    result = chi_square_check(mismatches, p0=0.02)
    assert result["verdict"] == "reject"
