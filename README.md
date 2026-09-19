# ENTANGLE, Teleportation-Based Quantum Digital Signature Threat Detection Framework

A simulation-based teleportation-based Quantum Digital Signature (QDS) threat-detection framework. It detects forgery, identity spoofing, and replay attacks against a physics-based signature protocol using real quantum circuits and closed-form statistics only, no AI, no ML, no trained models anywhere in the detection path.

## 1. Overview

Future Quantum Digital Signatures derive security from physical law, entanglement, teleportation, Pauli eigenstates, projective measurement, rather than computational hardness assumptions like RSA. ENTANGLE builds and tests a threat-detection layer for such a scheme end to end: real Qiskit circuits for the quantum protocol, a Sequential Probability Ratio Test (SPRT) for real-time statistical detection, and a nonce/counter classical channel for replay protection.

## 2. Problem Statement

Build a cyber threat detection framework for QDS that:
- detects forgery, identity spoofing, and replay attacks in real time
- includes a built-in attack simulator
- achieves low computational overhead with a mathematically stated security guarantee
- uses no AI/ML anywhere in the detection or decision path

## 3. Proposed Solution

Alice signs each round by teleporting a Pauli-eigenstate token to two independent verifiers (Bob, Charlie) over separately generated Bell pairs. Each verifier runs its own SPRT on its own measurement-mismatch stream. A simplified verifier-symmetrization rule combines their decisions. A nonce/counter classical channel independently blocks replay. Everything above is backed by real quantum circuits (not random-number approximations) and real, executed experiment results (not estimated ones), see Section 15.

## 4. Why Quantum

The detection principle is the same physical fact that underlies BB84 eavesdropping detection: no-cloning means an attacker cannot measure a quantum state without disturbing it. Intercepting a teleported qubit in transit necessarily perturbs the entangled pair, which shows up as an elevated mismatch rate at the verifier, this is what SPRT is watching for. This is why the quantum layer isn't decorative: remove it, and there is nothing left for the statistical layer to detect.

## 5. Architecture

```
ALICE (signer)
   |
BELL PAIR  (independently generated per verifier, no-cloning forbids reuse)
   |
TELEPORTATION  (Bell-basis measurement -> 2 classical bits)
   |
PAULI CORRECTION  (classically-conditioned gate on the verifier's qubit)
   |
BOB + CHARLIE  (independent projective measurement, basis announced after)
   |
MATCH / MISMATCH STREAM  (per verifier)
   |
SPRT  (per verifier, sequential)
   |
SIMPLIFIED SYMMETRIZATION
   |
FINAL SECURITY DECISION

EVE (attacker): intercept-resend | impersonation | replay
```

## 6. Roles

- **Alice**, signer; prepares the Pauli-eigenstate token and initiates each round.
- **Bob**, primary independent verifier.
- **Charlie**, second independent verifier (not a copy of Bob, see `tests/test_protocol.py::test_bob_and_charlie_are_independent_streams`).
- **Eve**, attacker; drives intercept-resend, impersonation, or replay.

## 7. Protocol Flow (per round)

1. Alice picks a random bit and a random Pauli basis (Z or X), prepares the token qubit accordingly.
2. A fresh Bell pair is generated between Alice and Bob (and, separately, Alice and Charlie).
3. Alice performs a Bell-basis measurement on (token qubit, her half of the pair) → 2 classical bits.
4. The verifier applies the corresponding Pauli correction (I, X, Z, or XZ) to their half of the pair, conditioned on those 2 bits, implemented as an actual classically-controlled gate in the Qiskit circuit (`qc.if_test`), not Python post-processing.
5. Alice announces the basis used. The verifier measures their (now-teleported) qubit in that basis.
6. Match/mismatch is recorded against Alice's intended bit.

## 8. Quantum Core

Built on Qiskit (`qiskit-aer`, `AerSimulator`). Every round executes a real 3-qubit circuit with mid-circuit measurement and classically-conditioned correction gates, see `src/quantum_core.py`. No probability shortcuts stand in for the physics.

**Signature token, defined precisely:** a single-qubit Pauli eigenstate. `token_bit ∈ {0,1}` and `token_basis ∈ {Z, X}` together select one of `{|0⟩, |1⟩, |+⟩, |−⟩}`. The verifier's expected result is `token_bit`, measured after teleportation in the basis Alice announces (`token_basis`). A **match** is verifier outcome == `token_bit`; anything else is a **mismatch**.

The dashboard shows the live signature token, basis, and expected outcomes for the current round in a "Signature Preparation, Alice" panel, so what Alice actually sent is visible during a run, not just Bob/Charlie's match/mismatch result.

**First success condition (tested, passing):** with no attacker and no noise, teleportation reconstructs the intended bit exactly, every round (`tests/test_quantum_core.py::test_honest_teleportation_exact_reconstruction`, 0/200 mismatches).

## 9. Attack Models

| Attack | Circuit-level mechanism | Requirement it addresses |
|---|---|---|
| Intercept-resend | Eve measures the verifier's half of the Bell pair in transit (own randomly chosen basis), resets it, and resends a freshly prepared qubit, implemented as real mid-circuit measure/reset/conditional-prepare gates | Forgery |
| Impersonation | The verifier's qubit is never entangled with Alice's token at all, no shared quantum resource exists | Identity spoofing |
| Replay | The classical (round_id, nonce, bits, tag) transcript from a prior round is resent | Replay |
| Cloning (Phase 2) | Eve entangles an ancilla with the verifier's qubit via a weak-measurement rotation and measures only the ancilla, partial information, partial disturbance, physically distinct from intercept-resend's full collapse | No-cloning theorem demonstration (Section 26) |

Replay is **not** a quantum-layer attack, no-cloning makes replaying a physical qubit impossible. What can be replayed is the classical announcement, so replay defense lives entirely in `src/classical_channel.py`, independent of the SPRT.

## 10. Calibration

Before any detection run, a no-attack calibration pass (120 rounds, real circuits, with the expected 5% physical noise applied) establishes the honest-channel baseline mismatch rate `p0`. SPRT's H0/H1 are derived from this, not hard-coded. See `simulator.py::calibrate`.

## 11. SPRT (sole gating detector)

Wald's Sequential Probability Ratio Test on the per-round mismatch stream. H0: honest channel (rate `p0`, from calibration). H1: attack (rate `p0 + 0.15`). Target error rates α = β = 0.01. Decision states: `continue`, `accept`, `reject`. The running log-likelihood ratio and both boundaries are tracked and displayed every round, see `src/detector.py`.

## 12. Simplified Symmetrization

Bob and Charlie each run an independent SPRT. Final decision: **accept only if both accept**; **reject if either rejects**; **a disagreement between the two is logged as suspicious**, not resolved by either verifier overriding the other.

> This prototype uses a simplified consistency-based verifier symmetrization mechanism rather than implementing the complete cryptographic symmetrization protocol from the QDS literature (Gottesman–Chuang and successors).

## 13. Chernoff-Hoeffding Bound

A closed-form upper bound on the probability that an attacker's induced disturbance stays under the detection margin for `n` rounds:

**P(false accept) ≤ exp(−2n·ε²)**

where ε is the gap between the honest baseline and the detection margin. With the parameters used in this prototype's experiments (n = 200, ε = 0.075): **P(false accept) ≤ 1.054 × 10⁻¹**. This is a theoretical statistical guarantee under the stated model and assumptions, it is not a claim of complete, formally proven QDS security (see Section 23).

## 14. Experiments

Five required experiments, run on the real circuit stack, repeated across 6 seeds for reproducibility:

1. Ideal honest channel (no attack, no noise)
2. Honest channel with physical noise (no attack)
3. Intercept-resend
4. Impersonation
5. Replay

## 15. Actual Results

From real, executed runs (`results/run_seed*.json`, none of these numbers are estimated):

| Seed | p0 (calibrated) | Clean | Noisy | Intercept-resend | Impersonation | Replay |
|---|---|---|---|---|---|---|
| 1 | 0.0292 | accept, 28 rounds | accept, 52 rounds, 3.9% mismatch | reject, 15 rounds, 26.7% mismatch | reject, 10 rounds, 70.0% mismatch | reject |
| 2 | 0.0167 | accept, 28 rounds | accept, 73 rounds, 4.1% mismatch | reject, 25 rounds, 32.0% mismatch | reject, 6 rounds, 66.7% mismatch | reject |
| 3 | 0.0083 | accept, 29 rounds | accept, 85 rounds, 3.5% mismatch | reject, 16 rounds, 18.8% mismatch | reject, 4 rounds, 50.0% mismatch | reject |
| 4 | 0.0208 | accept, 28 rounds | accept, 96 rounds, 5.2% mismatch | reject, 12 rounds, 25.0% mismatch | reject, 6 rounds, 50.0% mismatch | reject |
| 5 | 0.0083 | accept, 29 rounds | accept, 66 rounds, 0.0% mismatch | reject, 15 rounds, 20.0% mismatch | reject, 3 rounds, 66.7% mismatch | reject |
| 42 | 0.0250 | accept, 28 rounds | accept, 28 rounds, 0.0% mismatch | reject, 33 rounds, 15.2% mismatch | reject, 5 rounds, 60.0% mismatch | reject |

**Reading these results:** noise never triggers a false reject across any seed, this is the noise-vs-attack disambiguation the calibration step exists for. Intercept-resend mismatch rates cluster near the textbook ~25% BB84 intercept-resend statistic. Impersonation mismatch rates cluster near the ~50% expected for an uncorrelated guess. Replay is caught deterministically (not probabilistically) in 2 rounds every time, independent of the quantum-layer statistics.

## 16. Performance

Per-round circuit execution latency: ~1.6–5 ms/round (measured, `AerSimulator`, single shot). Full 5-experiment run including calibration completes in well under a second of quantum-simulation time.

## 17. Screenshots

Live dashboard: https://claude.ai/artifact/GdywRjeKZ3GQ5NQyBJ64ZY (see `assets/screenshots/` for captured stills once added).

## 18. Technology Stack

Python 3.12, Qiskit 2.x, qiskit-aer (`AerSimulator`), pytest. Dashboard: self-contained HTML/CSS/JS (no build step).

## 19. Installation

```bash
pip install -r requirements.txt
```

## 20. How to Run

```bash
# Run the full pytest suite
PYTHONPATH=src pytest tests/ -v

# Run all five experiments and save results
python src/simulator.py --all --seed 42 --save experiments/results/run.json

# Run a single mode
python src/simulator.py --mode intercept_resend --seed 1
python src/simulator.py --mode cloning --seed 1
python src/simulator.py --mode channel_tamper --seed 1   # Phase 2: MAC tamper demo
```

## 21. Repository Structure

See `docs/architecture.md` for the annotated version of the tree in the project root.

## 22. No-AI/ML Compliance

No component of this system uses a trained model, learned parameter, clustering, or classifier. All accept/reject decisions come from: (a) real quantum circuit execution and the physical consequence of disturbance under no-cloning, and (b) a closed-form sequential statistical test (SPRT) with thresholds set from a calibration measurement, never learned from labeled data.

## 23. Limitations

- Simplified verifier symmetrization, not the full cryptographic protocol (Section 12).
- The classical channel used for basis reconciliation and result comparison is **not authenticated** in this prototype (no Wegman-Carter MAC or equivalent), documented as a deliberate, known scope limitation in `docs/limitations.md`, not an oversight.
- Simulated, not physical, quantum hardware.
- This project is accurately described as **a simulation-based teleportation-based QDS threat-detection framework**, not a claim of complete real-world QDS security, formally proven security, or production readiness.

## 24. Future Scope

Full cryptographic symmetrization; authenticated classical channel; execution on real quantum hardware; extension to a third Pauli basis (Y) for a tighter security margin.

## 25. References

- Gottesman, D. & Chuang, I. (2001). *Quantum Digital Signatures.*
- Wald, A. (1945). *Sequential Tests of Statistical Hypotheses.*
- Bennett, C.H. & Brassard, G. (1984). *Quantum Cryptography: Public Key Distribution and Coin Tossing* (BB84).
- Hoeffding, W. (1963). *Probability Inequalities for Sums of Bounded Random Variables.*
- Clauser, Horne, Shimony & Holt (1969). *Proposed Experiment to Test Local Hidden-Variable Theories* (CHSH).
- Wegman, M. & Carter, J. (1981). *New Hash Functions and Their Use in Authentication and Set Equality.*
- Bužek, V. & Hillery, M. (1996). *Quantum Copying: Beyond the No-Cloning Theorem.*

## 26. Phase 2 Additions

Five items were explicitly out of core scope in Phase 1, to be added only after the core was working. All five were addressed; **none of them participate in the ACCEPT/THREAT decision**, that remains SPRT + symmetrization exactly as built in Phase 1.

| Item | Status | Notes |
|---|---|---|
| CHSH diagnostic panel | Done | Real measured S-value; honest ≈ 2.83–2.91 (near Tsirelson bound 2.828), degrades to ≈1.25–1.45 under intercept-resend. `docs/theory.md` explains why it's diagnostic, not gating. |
| Classical channel MAC + toggle | Done | Minimal universal-hash MAC (`WegmanCarterMAC`); detects transcript tampering as a distinct event type from replay. |
| Approximate cloning (4th attack) | Done | Weak-measurement/ancilla circuit, physically distinct from intercept-resend. Required re-tuning after an initial angle choice went undetected, see `docs/limitations.md` for that finding, disclosed rather than hidden. |
| Chi-square secondary check | Done | Cross-check on the same mismatch stream SPRT consumes; shown alongside the SPRT verdict in the CLI table and dashboard. |
| Bloom filter for replay cache | **Skipped** | Lowest-priority item; explicitly deferred per the addendum's own priority order. Current cache is a plain `set`, correct at this scale. |

Also fixed in this phase: a dashboard state-sync bug where the live panel and the completed-run history table could show inconsistent numbers after rapid clicking (overlapping, uncancelled `setTimeout` calls). Fixed by routing both displays through a single result object and adding run-state guarding.
