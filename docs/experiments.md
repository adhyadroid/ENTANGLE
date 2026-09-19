# Experiments

## Methodology

All five required experiments (`src/simulator.py`) run on the real Qiskit circuit stack described in `docs/architecture.md`, no step is approximated with a probability shortcut. Each run:

1. Executes a 120-round, no-attack calibration pass (with the expected 5% physical noise applied) to establish `p0`.
2. Runs up to 400 rounds of the requested mode, updating each verifier's SPRT every round, until the symmetrized decision leaves `continue`.
3. Records: total rounds used, per-verifier mismatch count/rate, final decision, verifier disagreements, per-round latency, total runtime.

Thresholds are derived from calibration, not chosen after seeing attack results.

## Results

See README Section 15 for the results table, and `experiments/results/run_seed*.json` for the raw, unedited output of each run (seeds 1–5, 42).

## Reproducing

```bash
python src/simulator.py --all --seed <any integer> --save experiments/results/run.json
```

Re-running with a new seed will produce different exact round counts (SPRT is sequential and stochastic) but the same qualitative pattern documented in README Section 15: clean/noisy always accept, intercept-resend/impersonation/replay always reject.
