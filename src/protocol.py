"""
protocol.py, ENTANGLE

Alice signs each round by teleporting a Pauli-eigenstate signature token to
Bob, and separately (a second independent Bell pair, no-cloning forbids
reusing one) to Charlie. Each verifier's qubit passes through its own real
Qiskit circuit (see quantum_core.py), including the attacker's circuit-level
manipulation when a mode requests it. Bob and Charlie each run their own
SPRT on their own mismatch stream.

Terminology: "signature token" always refers to the physical/quantum
Pauli-eigenstate object Alice prepares for a round. "Signature" alone
refers to the protocol's accept/reject outcome for that round (e.g.
"signature verified" / "signature rejected"), the two are not
interchangeable.

SIMPLIFIED SYMMETRIZATION (documented explicitly, not overstated):
This prototype uses a simplified consistency-based verifier symmetrization
mechanism rather than implementing the complete cryptographic
symmetrization protocol from the QDS literature (Gottesman-Chuang and
successors). Concretely: Bob and Charlie verify independently; the
signature is accepted only if both SPRTs say ACCEPT; if either rejects,
the final decision is REJECT; if they reach different terminal decisions,
that disagreement is itself logged as suspicious rather than resolved by
letting one verifier override the other.
"""

import random
from dataclasses import dataclass

from quantum_core import run_round, approximate_cloning_round
from attacks import circuit_kwargs_for
from detector import SPRT

_TOKEN_STATES = {("Z", 0): "|0⟩", ("Z", 1): "|1⟩", ("X", 0): "|+⟩", ("X", 1): "|−⟩"}


@dataclass
class RoundRecord:
    round_id: int
    intended_bit: int
    basis: str
    bob_bit: int
    charlie_bit: int
    bob_mismatch: bool
    charlie_mismatch: bool
    bob_decision: str
    charlie_decision: str
    symmetrized_decision: str
    disagreement: bool
    # Exposed for the dashboard's Signature Preparation panel, these are
    # not new computations, just named views onto data already produced
    # above (see docs/protocol.md).
    token_state: str          # e.g. "|+⟩", the Pauli eigenstate Alice prepared
    valid_token: bool         # False only for impersonation: no legitimate
                               # Alice-originated token exists for that round
    expected_bob: int         # what Bob should measure if honest (== intended_bit)
    expected_charlie: int     # what Charlie should measure if honest (== intended_bit)


def run_protocol_round(round_id: int, attack_mode: str, bob_sprt: SPRT,
                        charlie_sprt: SPRT, noise_prob: float = 0.0,
                        rng: random.Random = None) -> RoundRecord:
    rng = rng or random
    intended_bit = rng.choice([0, 1])
    basis = rng.choice(["Z", "X"])
    round_noise = noise_prob if attack_mode == "noisy" else 0.0

    if attack_mode == "cloning":
        bob_bit = approximate_cloning_round(intended_bit, basis, basis)
        charlie_bit = approximate_cloning_round(intended_bit, basis, basis)
    else:
        kwargs = circuit_kwargs_for(attack_mode)
        bob_bit = run_round(intended_bit, basis, basis, noise_prob=round_noise,
                             eve_basis=rng.choice(["Z", "X"]), **kwargs)
        charlie_bit = run_round(intended_bit, basis, basis, noise_prob=round_noise,
                                 eve_basis=rng.choice(["Z", "X"]), **kwargs)

    bob_mismatch = bob_bit != intended_bit
    charlie_mismatch = charlie_bit != intended_bit

    bob_result = bob_sprt.update(bob_mismatch)
    charlie_result = charlie_sprt.update(charlie_mismatch)

    disagreement = (
        bob_result.decision in ("accept", "reject")
        and charlie_result.decision in ("accept", "reject")
        and bob_result.decision != charlie_result.decision
    )

    if bob_result.decision == "continue" or charlie_result.decision == "continue":
        symmetrized = "continue"
    elif bob_result.decision == "accept" and charlie_result.decision == "accept":
        symmetrized = "accept"
    else:
        symmetrized = "reject"

    return RoundRecord(
        round_id=round_id, intended_bit=intended_bit, basis=basis,
        bob_bit=bob_bit, charlie_bit=charlie_bit,
        bob_mismatch=bob_mismatch, charlie_mismatch=charlie_mismatch,
        bob_decision=bob_result.decision, charlie_decision=charlie_result.decision,
        symmetrized_decision=symmetrized, disagreement=disagreement,
        token_state=_TOKEN_STATES[(basis, intended_bit)],
        valid_token=(attack_mode != "impersonation"),
        expected_bob=intended_bit, expected_charlie=intended_bit,
    )
