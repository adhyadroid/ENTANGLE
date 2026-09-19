# Protocol & Theory

Every concept below is used directly in `src/`; nothing here is background padding.

**Qubit**, the basic unit of quantum information; a 2-level system, here always a Pauli eigenstate (see below). Implemented as a Qiskit qubit.

**Bell state / entanglement**, a 2-qubit state, `(|00⟩+|11⟩)/√2`, that cannot be written as a product of two independent single-qubit states. Built in `quantum_core.build_round_circuit` via `H` then `CX`. Alice and each verifier share one Bell pair per round; a fresh pair is generated per verifier since no-cloning forbids splitting one pair's correlations across two recipients.

**Quantum teleportation**, transmits an unknown qubit's state using a shared Bell pair plus 2 classical bits, without physically moving the qubit. Implemented exactly as the textbook 3-qubit circuit: CNOT + Hadamard on (token, Alice's half), measure both, classically-conditioned correction on the verifier's half.

**Bell-basis measurement**, projecting two qubits onto the 4 Bell states, implemented as CNOT+H followed by computational-basis measurement (the standard disentangling trick).

**Pauli operators (I, X, Z)**, the correction gates applied to the verifier's qubit, chosen by the 2 classical bits from the Bell measurement. `X` and `Z` also generate the Z-basis (`{|0⟩,|1⟩}`) and X-basis (`{|+⟩,|−⟩}`) eigenstates used for the signature token.

**Pauli eigenstates**, the 4 states `{|0⟩,|1⟩,|+⟩,|−⟩}`. The signature token is always one of these, selected by `(token_bit, token_basis)`.

**Projective measurement**, collapses a qubit onto one of two basis outcomes with the standard Born-rule probability. Every `qc.measure` call in this codebase is a real projective measurement, not a classical random draw standing in for one.

**QDS (Quantum Digital Signature)**, a signature scheme whose unforgeability derives from quantum physical laws (no-cloning, non-orthogonal-state indistinguishability) rather than computational hardness.

**Verification**, the verifier measures the teleported qubit in the basis Alice announces after the fact, and compares to the intended bit.

**Symmetrization**, see `docs/security_analysis.md` and README Section 12; this prototype's simplified version requires both Bob and Charlie to independently accept.

**Quantum disturbance**, the physical fact that measuring or intercepting a quantum state in the "wrong" basis perturbs it; the statistical basis for every attack this framework detects.

**Mismatch rate**, fraction of rounds where a verifier's measured bit disagrees with Alice's intended bit.

**Calibration**, a no-attack run establishing the honest-channel baseline mismatch rate (`p0`), used to set SPRT's hypotheses.

**SPRT**, see `docs/security_analysis.md`.

**Chernoff-Hoeffding bound**, see `docs/security_analysis.md`.

**Intercept-resend, impersonation, replay**, see README Section 9 and `docs/limitations.md`.

**CHSH / Bell inequality (Phase 2, diagnostic only)**, a statistical test of whether measurement correlations between two qubits exceed what any local-hidden-variable (classical) theory could produce. `S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′)` over four measurement-angle pairs; the classical bound is S ≤ 2, and quantum mechanics allows up to S = 2√2 ≈ 2.828 (Tsirelson's bound). Shown in the dashboard as an "entanglement quality" readout, computed from real measurement statistics on the same Bell-pair generation the protocol already uses. **It is not the detection mechanism**, the signature token's mismatch rate (fed to SPRT) is a different, separate security property. CHSH tests device-independent entanglement quality; the SPRT tests whether *this specific signed token* was tampered with. A system could in principle have healthy CHSH correlations on its raw Bell pairs while still needing the mismatch-rate test to catch token-specific tampering, which is why CHSH is diagnostic rather than gating here.

**No-cloning theorem (Phase 2, cloning attack)**, an unknown quantum state cannot be copied perfectly. This is why intercept-resend (which effectively destroys and replaces the original) and approximate cloning (which extracts partial information via a weak measurement, leaving a degraded-but-still-there qubit) are physically distinct attacks with different disturbance signatures, rather than the same attack in two names.
