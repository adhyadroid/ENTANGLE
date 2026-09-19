# Protocol Walkthrough

## What Alice sends

One Pauli-eigenstate qubit per round: `(token_bit ∈ {0,1}, token_basis ∈ {Z,X})`, teleported to each verifier over a freshly generated Bell pair.

## What Bob/Charlie expect

The verifier expects, after correction, to measure `token_bit` when measuring in `token_basis`, the basis Alice announces only after the teleportation and correction steps are complete (standard basis-reconciliation ordering).

## What they measure

A projective measurement outcome in `{0,1}`, obtained by a real `qc.measure` call on the teleported-and-corrected qubit (`quantum_core.run_round`).

## What counts as a match / mismatch

`match`: verifier's measured bit == `token_bit`. `mismatch`: anything else. This single bit feeds directly into that verifier's SPRT (`detector.SPRT.update`).

## Round sequence

1. `protocol.run_protocol_round` picks `(intended_bit, basis)` at random.
2. `attacks.circuit_kwargs_for(mode)` resolves the attack mode to circuit parameters.
3. `quantum_core.run_round` is called twice, once for Bob, once for Charlie, each with an independently generated Bell pair and (for intercept-resend) an independently, randomly chosen Eve basis.
4. Each verifier's mismatch is fed into its own `SPRT`.
5. `symmetrize(bob_decision, charlie_decision)` produces the round's overall decision, per the rule in README Section 12.

Separately, `classical_channel.ClassicalChannel` binds every round's classical announcement to a monotonic counter and a hash tag, and independently rejects replayed transcripts regardless of what the quantum-layer SPRT concludes.

## Dashboard: Signature Preparation panel

The dashboard shows a "SIGNATURE PREPARATION, ALICE" panel above the attack-mode selector, populated from the same round data described above (`RoundRecord.token_state`, `.basis`, `.expected_bob`, `.expected_charlie`). It updates on the same per-round refresh as the rest of the status panel, so the two can never show inconsistent numbers. In impersonation mode it shows "No valid Alice signature token" instead of a normal token, since no real Alice-originated token exists for that round. In replay mode it shows which original round is being replayed.
