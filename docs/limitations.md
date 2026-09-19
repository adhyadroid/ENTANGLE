# Limitations

This project is accurately described as **a simulation-based teleportation-based Quantum Digital Signature threat-detection framework**. It does not claim complete real-world QDS security, formally proven security, or production readiness.

## Known, deliberate scope limitations

- **Unauthenticated classical channel.** This prototype does not authenticate the classical channel used for basis reconciliation and result comparison (e.g. via Wegman-Carter MACs or an equivalent information-theoretic MAC), which a production deployment would require to close a man-in-the-middle gap during that exchange. This is a stated, deliberate scope decision, not an oversight.
- **Simplified verifier symmetrization**, not the full cryptographic symmetrization protocol from the QDS literature (see `docs/security_analysis.md`).
- **Simulated quantum hardware** (Qiskit Aer), not physical qubits, a production system would need to characterize real hardware noise, which differs from the bit-flip noise model used here.
- **Two Pauli bases only** (Z, X); a third (Y) basis was not implemented and would tighten the security margin further if added.
- **Excluded by deliberate design** (not because they don't exist as valid techniques, but because they were out of scope for this prototype): CHSH inequality monitoring, chi-squared/KS tests, approximate-cloning attack simulation, Bloom filters, full Wegman-Carter MAC implementation. See README Section 23 and the project's architecture decision record for why.

## What the Chernoff-Hoeffding bound assumes

The bound in `docs/security_analysis.md` assumes i.i.d. rounds and an attacker whose induced disturbance is bounded below by a fixed, known ε. It does not account for an adaptive attacker who varies strategy across rounds, nor for correlated noise across rounds.

## A real finding from tuning the Phase 2 cloning attack (documented honestly, not fixed by hiding it)

While tuning the approximate-cloning attack's weak-measurement angle, an early choice (`weak_angle = π/4`, true mismatch rate ≈ 13%) was **not reliably detected**, across 8 seeds, SPRT reached "accept" every time, because the attack's true disturbance sat below `p1 = p0 + ATTACK_MARGIN` (≈ 17–20%). This is not a bug in the circuit or the SPRT logic; it is exactly what the Hoeffding bound in `docs/security_analysis.md` predicts: **detection is only guaranteed when the attacker's disturbance exceeds the stated margin ε.** An attack weak enough to stay under that margin is, by the framework's own stated math, not guaranteed to be caught, and empirically, it wasn't.

The angle was retuned (`weak_angle = 0.9π`, true mismatch rate ≈ 20–25%) to sit clearly above the margin, and detection became reliable across 8 seeds. This is disclosed here rather than silently fixed and forgotten because it is a genuine illustration of the security model's actual guarantees and their actual limits, a production deployment would need to choose `ATTACK_MARGIN` based on the weakest attack it needs to guarantee catching, accepting a slower (more-rounds) detection in exchange for a tighter margin.
