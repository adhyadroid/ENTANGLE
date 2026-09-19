# Security Analysis

## SPRT, sole gating decision method

Wald's Sequential Probability Ratio Test on the per-round mismatch stream (`src/detector.py::SPRT`).

- **H0** (honest): mismatch probability `p0`, from a real no-attack calibration run (`simulator.calibrate`).
- **H1** (attack): mismatch probability `p1 = min(p0 + 0.15, 0.45)`.
- Target error rates: α = 0.01 (false-positive: reject an honest signature), β = 0.01 (false-negative: accept a forged one).
- Boundaries: `upper = ln((1−β)/α)`, `lower = ln(β/(1−α))`.
- Each round updates the running log-likelihood ratio; crossing `upper` → reject, crossing `lower` → accept, otherwise continue. This gives genuinely sequential, early-stopping decisions, the actual mechanism "real-time detection" requires, as opposed to a fixed-sample batch test.

No other statistical test (chi-square, KS, CHSH) sits in the decision path, this is deliberate scope, see `docs/limitations.md`.

## Chernoff-Hoeffding bound

For `n` independent rounds with true honest mismatch rate `p0` and a detection margin `ε` below the attack rate, Hoeffding's inequality bounds the probability that an attacker's induced disturbance stays under the detection threshold for all `n` rounds:

**P(false accept) ≤ exp(−2n·ε²)**

With this prototype's parameters (`n = 200`, `ε = ATTACK_MARGIN/2 = 0.075`):

**P(false accept) ≤ exp(−2·200·0.075²) ≈ 1.054 × 10⁻¹**

This is computed once from the stated parameters (`simulator.py`, `hoeffding_false_accept_bound`), not fitted to make a graph look favorable, and not re-derived live for show.

**What this bound does and does not claim:** it is a theoretical statistical guarantee under the stated model, a fixed, known `ε`, i.i.d. rounds, and an attacker whose induced disturbance is bounded below by `ε`, not a proof that the complete QDS system is secure against every possible attack strategy or that it is production-ready. See `docs/limitations.md` for the assumptions this bound depends on.

## Simplified verifier symmetrization

Full cryptographic symmetrization (Gottesman-Chuang and successors) gives QDS its transferability and non-repudiation properties: no single verifier can unilaterally accept a forgery or cause repudiation of a valid signature. This prototype implements a simplified stand-in:

- Bob and Charlie each run an independent SPRT on an independently generated Bell pair.
- Final decision: accept only if both accept; reject if either rejects.
- A disagreement between Bob and Charlie's terminal decisions is logged as suspicious, not resolved by either party overriding the other.

This is explicitly not claimed to be the complete cryptographic protocol from the literature.

## Phase 2 diagnostic additions (non-gating)

The following are informational/diagnostic only, none of them feed the ACCEPT/THREAT decision, which remains SPRT + symmetrization exactly as above.

- **CHSH diagnostic** (`quantum_core.chsh_s_value`), real, measured Bell-inequality correlation on the protocol's own Bell pairs. Tests entanglement quality, a different security property from token-mismatch detection (see `docs/theory.md`).
- **Chi-square secondary check** (`detector.chi_square_check`), a goodness-of-fit test on the identical mismatch data SPRT already consumed, shown alongside the SPRT verdict as a robustness cross-check. If the two diverge, that is worth investigating (see `docs/limitations.md` for one real instance of exactly this kind of divergence surfacing a genuine parameter-tuning issue during development).
- **Classical channel MAC** (`classical_channel.WegmanCarterMAC`), a minimal universal-hash MAC detecting tampering with a classical message in transit, a distinct threat (MITM on basis reconciliation) from replay. Toggleable in the dashboard.
- **Approximate cloning** (`quantum_core.approximate_cloning_round`), a 4th attack mode, physically distinct from intercept-resend (partial/weak measurement via an ancilla qubit rather than a full projective measurement + resend), producing a measurably different, generally lower mismatch signature. Runs through the identical SPRT pipeline as the other three attacks.
- **Bloom filter for the replay cache**, explicitly *not* implemented in this submission. It was the lowest-priority Phase 2 item and was skipped when time ran out, per the addendum's own stated priority order ("skip first if short on time"). The current replay cache is a plain Python `set` of seen tags, which is correct at this scale but would need a space/false-positive-rate tradeoff decision (a Bloom filter's false-positive risk means occasionally, incorrectly, flagging a legitimate transcript as replayed) to scale further.
