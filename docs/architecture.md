# Architecture

```
entangle/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── config.py
│
├── src/
│   ├── quantum_core.py       # real Qiskit circuits: Bell pair, teleportation, correction, Eve
│   ├── protocol.py           # Alice/Bob/Charlie round loop, symmetrization
│   ├── classical_channel.py  # nonce/counter, replay detection
│   ├── detector.py           # SPRT, calibration, Hoeffding bound
│   ├── attacks.py            # attack-mode -> circuit-parameter mapping
│   └── simulator.py          # calibration + experiment runner
│
├── dashboard/
│   └── index.html            # self-contained interactive dashboard
│
├── experiments/
│   └── results/              # JSON output of real experiment runs
│
├── tests/
│   ├── test_quantum_core.py
│   ├── test_protocol.py
│   ├── test_detector.py
│   ├── test_attacks.py
│   ├── test_replay.py
│   └── test_phase2.py         # CHSH, cloning, MAC, chi-square (Phase 2)
│
├── docs/
│   ├── protocol.md
│   ├── theory.md
│   ├── security_analysis.md
│   ├── experiments.md
│   └── limitations.md
│
└── presentation/
    └── presentation.md
```

## Data flow, per round

```
Alice: pick (bit, basis) -> prepare token qubit
   -> generate Bell pair (per verifier)
   -> [attack mode determines circuit variant here]
   -> Bell-basis measurement on (token, Alice's half) -> 2 classical bits
   -> classically-conditioned Pauli correction on verifier's half
   -> verifier measures in announced basis -> match/mismatch
   -> SPRT.update(mismatch) -> continue/accept/reject   (per verifier)
   -> symmetrize(bob_decision, charlie_decision) -> FINAL SECURITY DECISION
```

Replay protection runs on a separate path entirely: `classical_channel.ClassicalChannel` binds each round to a monotonic counter and a nonce-derived tag, independent of the quantum-layer SPRT decision.

```
                    ┌───────────────────────────────────┐
                    │   PHASE 2, DIAGNOSTICS (non-gating)│
                    │                                     │
   Bell pairs  ───► │  CHSH S-value (entanglement quality)│
   (reused,         │  Chi-square secondary check         │──► diagnostics / logging
   read-only)       │  (cross-checks SPRT's own data)      │    (dashboard panel,
                    │                                     │     docs, JSON output)
   classical   ───► │  WegmanCarterMAC (tamper detection) │
   messages          └───────────────────────────────────┘
                              (nothing here feeds back into
                               the FINAL SECURITY DECISION box above)
```

The approximate-cloning attack (Phase 2) is not a diagnostic, it is a 4th attack mode that runs through the same SPRT/symmetrization pipeline as the other three, shown in the round-flow diagram above like any other attack mode.
