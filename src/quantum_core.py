"""
quantum_core.py, ENTANGLE

Real Qiskit circuits. Every round below executes an actual quantum circuit
on Qiskit's Aer simulator: Bell-pair generation, quantum teleportation with
mid-circuit Bell-basis measurement, classically-conditioned Pauli
correction, and a final projective measurement in a chosen Pauli eigenbasis
(Z or X). No AI/ML. No probability shortcuts standing in for the physics.

Qubit layout: q0 = Alice's signature token, q1 = Alice's half of the Bell
pair, q2 = Bob's (or Charlie's) half.
"""

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import numpy as np

_SIM = AerSimulator(method="automatic")


def _prepare(qc: QuantumCircuit, qubit, bit: int, basis: str):
    """Prepare a Pauli eigenstate: bit in {0,1}, basis in {'Z','X'}."""
    if bit == 1:
        qc.x(qubit)
    if basis == "X":
        qc.h(qubit)


def build_round_circuit(token_bit: int, token_basis: str, verify_basis: str,
                         eve_intercept: bool = False, eve_basis: str = "Z",
                         no_entanglement: bool = False, noise_prob: float = 0.0,
                         rng=None) -> QuantumCircuit:
    """
    Build one full round's circuit.

    no_entanglement=True models IMPERSONATION: the receiving qubit (q2) is
    never entangled with Alice's token at all, the impersonator has no
    real shared quantum resource, so q2 is prepared as an arbitrary guess,
    uncorrelated with Alice's actual token.

    noise_prob applies a physical bit-flip error gate (qc.x) to the
    verifier's qubit with the given probability, right before its final
    measurement, a real circuit-level noise channel, present whether or
    not an attacker is active, distinct from any attack.
    """
    import random as _random
    rng = rng or _random
    q = QuantumRegister(3, "q")
    c_bell = ClassicalRegister(2, "bell")      # Alice's Bell-measurement bits
    c_eve = ClassicalRegister(1, "eve")        # Eve's intercepted outcome, if any
    c_result = ClassicalRegister(1, "result")  # verifier's final measurement
    qc = QuantumCircuit(q, c_bell, c_eve, c_result)

    _prepare(qc, q[0], token_bit, token_basis)  # Alice's signature token

    if no_entanglement:
        _prepare(qc, q[2], 0, "Z")  # impersonator's arbitrary guess qubit
        if noise_prob > 0 and rng.random() < noise_prob:
            qc.x(q[2])
        if verify_basis == "X":
            qc.h(q[2])
        qc.measure(q[2], c_result[0])
        return qc

    # Bell pair distribution: q1 (Alice's half) <-> q2 (verifier's half)
    qc.h(q[1])
    qc.cx(q[1], q[2])

    if eve_intercept:
        # Eve intercepts q2 in transit: measures it in her own basis, then
        # resends a freshly prepared qubit, destroys entanglement.
        if eve_basis == "X":
            qc.h(q[2])
        qc.measure(q[2], c_eve[0])
        qc.reset(q[2])
        with qc.if_test((c_eve, 1)):
            qc.x(q[2])
        if eve_basis == "X":
            qc.h(q[2])

    # Teleportation: Bell-basis measurement on (q0, q1)
    qc.cx(q[0], q[1])
    qc.h(q[0])
    qc.measure(q[0], c_bell[0])
    qc.measure(q[1], c_bell[1])

    # Pauli correction on q2, conditioned on the classical bits.
    # c_bell[0] = outcome of q0 (message qubit, measured after H)
    # c_bell[1] = outcome of q1 (Alice's Bell-pair half, measured after CNOT)
    # register integer = c_bell[0] + 2*c_bell[1] (bit 0 is least-significant)
    # (m0,m1)=(0,1) -> int 2 (0b10) -> apply X
    # (m0,m1)=(1,0) -> int 1 (0b01) -> apply Z
    # (m0,m1)=(1,1) -> int 3 (0b11) -> apply X and Z (order irrelevant: differs
    #                                   only by an unobservable global phase)
    with qc.if_test((c_bell, 0b10)):
        qc.x(q[2])
    with qc.if_test((c_bell, 0b01)):
        qc.z(q[2])
    with qc.if_test((c_bell, 0b11)):
        qc.x(q[2])
        qc.z(q[2])

    # Verifier's projective measurement, in the basis Alice announces after
    if noise_prob > 0 and rng.random() < noise_prob:
        qc.x(q[2])  # physical bit-flip noise, independent of any attacker
    if verify_basis == "X":
        qc.h(q[2])
    qc.measure(q[2], c_result[0])
    return qc


def run_round(token_bit: int, token_basis: str, verify_basis: str,
              eve_intercept: bool = False, eve_basis: str = "Z",
              no_entanglement: bool = False, noise_prob: float = 0.0,
              rng=None) -> int:
    """Execute one round's circuit, return the verifier's measured bit."""
    qc = build_round_circuit(token_bit, token_basis, verify_basis,
                              eve_intercept, eve_basis, no_entanglement,
                              noise_prob, rng)
    result = _SIM.run(qc, shots=1).result()
    counts = result.get_counts()
    bitstring = next(iter(counts.keys()))
    result_bit = int(bitstring.split()[0])  # 'result' register reported first
    return result_bit


# ---------------------------------------------------------------------------
# PHASE 2 (diagnostic / non-gating additions, see docs/limitations.md and
# docs/theory.md for why none of the functions below feed the SPRT decision)
# ---------------------------------------------------------------------------

_ANGLES = {"a": 0.0, "a2": np.pi / 2, "b": np.pi / 4, "b2": 3 * np.pi / 4}


def _chsh_correlation_circuit(angle_a: float, angle_b: float, eve_intercept: bool = False):
    """A dedicated 2-qubit Bell-pair circuit (independent of the teleportation
    circuit) with rotated measurement bases, for a CHSH correlation test.
    Diagnostic only, this measures entanglement quality, not the signature
    token's mismatch rate, and is never used to decide accept/reject."""
    q = QuantumRegister(2, "q")
    c_eve = ClassicalRegister(1, "eve")
    c = ClassicalRegister(2, "c")
    qc = QuantumCircuit(q, c_eve, c)
    qc.h(q[0])
    qc.cx(q[0], q[1])
    if eve_intercept:
        qc.measure(q[1], c_eve[0])
        qc.reset(q[1])
        with qc.if_test((c_eve, 1)):
            qc.x(q[1])
    qc.ry(-angle_a, q[0])
    qc.ry(-angle_b, q[1])
    qc.measure(q[0], c[0])
    qc.measure(q[1], c[1])
    return qc


def chsh_s_value(eve_intercept: bool = False, shots: int = 400) -> float:
    """Real CHSH S-value from actual measurement statistics (4 settings
    pairs, `shots` runs each), not a hardcoded or estimated number."""
    def correlation(angle_a, angle_b):
        qc = _chsh_correlation_circuit(angle_a, angle_b, eve_intercept)
        result = _SIM.run(qc, shots=shots).result()
        counts = result.get_counts()
        total = sum(counts.values())
        # the 2-bit joint-outcome register prints first in the counts key
        # (Qiskit prints registers in reverse declaration order); its two
        # characters are q1's and q0's outcome bits.
        agree = sum(v for k, v in counts.items() if k.split()[0].count("1") % 2 == 0)
        return (2 * agree / total) - 1  # E(a,b) in [-1, 1]

    e_ab = correlation(_ANGLES["a"], _ANGLES["b"])
    e_ab2 = correlation(_ANGLES["a"], _ANGLES["b2"])
    e_a2b = correlation(_ANGLES["a2"], _ANGLES["b"])
    e_a2b2 = correlation(_ANGLES["a2"], _ANGLES["b2"])
    return abs(e_ab - e_ab2 + e_a2b + e_a2b2)


def approximate_cloning_round(token_bit: int, token_basis: str, verify_basis: str,
                               weak_angle: float = 0.9 * np.pi, rng=None) -> int:
    """
    APPROXIMATE CLONING ATTACK (Phase 2, attack mode #4).

    Perfect cloning of an unknown qubit is forbidden by the no-cloning
    theorem, Eve cannot get a full, undisturbed copy the way she could
    with classical data. What she CAN do is an imperfect, partial-
    information "weak measurement": entangle an ancilla with the in-transit
    qubit via a small-angle controlled rotation, then measure only the
    ancilla. This extracts partial information about the qubit without
    fully collapsing it (unlike intercept-resend's full projective
    measurement + resend), producing a weaker but still nonzero
    disturbance, a different, smaller mismatch signature than
    intercept-resend, which is precisely what makes it worth distinguishing
    from intercept-resend in the experiment set.
    """
    q = QuantumRegister(4, "q")  # q0=token, q1=alice_half, q2=bob_half, q3=Eve's ancilla
    c_bell = ClassicalRegister(2, "bell")
    c_eve = ClassicalRegister(1, "eve")
    c_result = ClassicalRegister(1, "result")
    qc = QuantumCircuit(q, c_bell, c_eve, c_result)

    _prepare(qc, q[0], token_bit, token_basis)
    qc.h(q[1])
    qc.cx(q[1], q[2])

    # Eve's weak measurement / approximate-cloning attempt on q2 in transit
    qc.cry(weak_angle, q[2], q[3])
    qc.measure(q[3], c_eve[0])  # Eve's partial-information outcome; q2 is
                                 # NOT reset or replaced, it remains the
                                 # same (now partially disturbed) qubit.

    qc.cx(q[0], q[1])
    qc.h(q[0])
    qc.measure(q[0], c_bell[0])
    qc.measure(q[1], c_bell[1])
    with qc.if_test((c_bell, 0b10)):
        qc.x(q[2])
    with qc.if_test((c_bell, 0b01)):
        qc.z(q[2])
    with qc.if_test((c_bell, 0b11)):
        qc.x(q[2])
        qc.z(q[2])
    if verify_basis == "X":
        qc.h(q[2])
    qc.measure(q[2], c_result[0])

    result = _SIM.run(qc, shots=1).result()
    counts = result.get_counts()
    bitstring = next(iter(counts.keys()))
    return int(bitstring.split()[0])
