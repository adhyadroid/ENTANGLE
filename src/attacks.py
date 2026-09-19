"""
attacks.py, ENTANGLE

Each attack mode maps to real circuit-level parameters consumed by
quantum_core.run_round, not a post-hoc probability adjustment. The circuit
that executes for "intercept_resend" is a physically different circuit
(with Eve's measure/reset/resend inserted) from the honest circuit; the
circuit for "impersonation" never entangles the verifier's qubit with
Alice's token at all. Replay is not a quantum-layer attack at all (see
classical_channel.py), no-cloning makes replaying a qubit impossible;
what gets replayed is the classical transcript.
"""

ATTACK_MODES = {
    "clean": dict(eve_intercept=False, no_entanglement=False),
    "noisy": dict(eve_intercept=False, no_entanglement=False),  # noise applied separately, see protocol.py
    "intercept_resend": dict(eve_intercept=True, no_entanglement=False),
    "impersonation": dict(eve_intercept=False, no_entanglement=True),
    # "cloning" is handled separately in protocol.py, it calls
    # quantum_core.approximate_cloning_round directly, a distinct circuit
    # (with an Eve ancilla qubit) rather than a variant of run_round's
    # eve_intercept/no_entanglement flags.
}


def circuit_kwargs_for(mode: str) -> dict:
    if mode not in ATTACK_MODES:
        raise ValueError(f"unknown attack mode: {mode}")
    return ATTACK_MODES[mode]
