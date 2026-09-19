# ENTANGLE, Presentation Content

## Slide 1, Title
**ENTANGLE**
Teleportation-Based Quantum Digital Signature Threat Detection Framework
*Visual:* dashboard hero screenshot (dark, serif "ENTANGLE" wordmark).
*Speaker notes:* Introduce the team and the one-line pitch: real quantum circuits, real statistics, zero AI.

## Slide 2, Problem
Future Quantum Digital Signatures rely on physics, not math, but nobody's built the threat detection layer to protect them.
- Forgery, spoofing, and replay all need distinct detection strategies
- AI/ML is explicitly disallowed for this challenge
*Visual:* simple 3-icon row (forgery / spoofing / replay).
*Speaker notes:* Ground the audience in why "no AI" is a real constraint, not a gimmick, it forces the detection logic to be provably grounded in physics and statistics.

## Slide 3, Proposed Solution
Teleport a Pauli-eigenstate signature token to two independent verifiers; detect tampering via SPRT on the resulting mismatch rate.
*Visual:* the protocol chain (Alice → Bell Pair → Teleportation → Pauli Correction → Bob+Charlie → SPRT → Decision).
*Speaker notes:* One sentence each on why teleportation (physical detection surface) and why SPRT (real-time, sequential, closed-form).

## Slide 4, Architecture
*Visual:* the architecture diagram from `docs/architecture.md`, protocol chain + module map side by side.
*Speaker notes:* Walk left to right: quantum core → protocol/symmetrization → detector → classical channel, each backed by its own test file.

## Slide 5, Quantum Protocol
Real Qiskit circuits: Bell pair, mid-circuit Bell measurement, classically-conditioned Pauli correction, not random-number approximations.
*Visual:* the actual circuit diagram (`qc.draw()` output) for one round.
*Speaker notes:* Point out the `if_test` blocks specifically, this is the "actual quantum circuit" requirement, visibly satisfied.

## Slide 6, Threat Detection
Three attacks, three distinct circuit-level mechanisms: intercept-resend, impersonation, replay (classical-channel only).
*Visual:* the attack table from README Section 9.
*Speaker notes:* Emphasize replay is deliberately *not* a quantum attack, no-cloning makes that physically impossible, and that's a design choice, not a gap.

## Slide 7, Experiments & Results
Real, executed results across 6 seeds: clean/noisy always accept; intercept-resend/impersonation/replay always reject.
*Visual:* the results table from README Section 15.
*Speaker notes:* Highlight the noisy-channel row specifically, this is the noise-vs-attack disambiguation proof.

## Slide 8, Dashboard / Demo
Live protocol trace, SPRT likelihood ratio and boundaries, symmetrization result, nonce/counter status.
*Visual:* dashboard screenshot mid-run.
*Speaker notes:* Run the live demo here if time allows; otherwise narrate the screenshot.

## Slide 9, Security Analysis
SPRT thresholds from real calibration; Chernoff-Hoeffding bound: P(false accept) ≤ 1.054×10⁻¹ at n=200, ε=0.075.
*Visual:* the bound formula, stated plainly.
*Speaker notes:* State clearly what this bound does and doesn't claim, a stated-model guarantee, not "the system is provably secure."

## Slide 10, Impact, Limitations, Future Scope
Simplified symmetrization, unauthenticated classical channel, both named explicitly, not hidden.
*Visual:* two-column "what's in scope / what's deliberately out" from `docs/limitations.md`.
*Speaker notes:* Close on honesty as a feature: every exclusion here was a documented decision, not a gap someone might find and use against the team.
