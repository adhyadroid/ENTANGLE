"""
simulator.py, ENTANGLE

Runs the calibration pass, then each of the five required experiments, and
prints a results table with real numbers from real circuit executions:
total rounds, mismatches, mismatch rate, detection result, rounds-to-
decision, and per-round latency.

Usage:
    python simulator.py --all
    python simulator.py --mode clean|noisy|intercept_resend|impersonation|replay
"""

import argparse
import json
import random
import time
from pathlib import Path

from detector import SPRT, calibrate_baseline, hoeffding_false_accept_bound, chi_square_check
from protocol import run_protocol_round
from classical_channel import ClassicalChannel, WegmanCarterMAC
from quantum_core import chsh_s_value

MAX_ROUNDS = 400
ALPHA = 0.01
BETA = 0.01
ATTACK_MARGIN = 0.15
EXPECTED_CHANNEL_NOISE = 0.05


def calibrate(rng, n_rounds: int = 120, noise_prob: float = EXPECTED_CHANNEL_NOISE) -> float:
    """No-attack calibration pass, WITH expected physical noise, -> honest baseline p0."""
    dummy_bob, dummy_charlie = SPRT(1e-3, 0.5), SPRT(1e-3, 0.5)
    mismatches = []
    for i in range(n_rounds):
        rec = run_protocol_round(i, "noisy", dummy_bob, dummy_charlie,
                                  noise_prob=noise_prob, rng=rng)
        mismatches.append(rec.bob_mismatch)
        mismatches.append(rec.charlie_mismatch)
    return calibrate_baseline(mismatches)


def run_experiment(mode: str, p0: float, rng) -> dict:
    p1 = min(p0 + ATTACK_MARGIN, 0.45)
    bob_sprt = SPRT(p0, p1, ALPHA, BETA)
    charlie_sprt = SPRT(p0, p1, ALPHA, BETA)

    noise = EXPECTED_CHANNEL_NOISE if mode == "noisy" else 0.0
    start = time.perf_counter()
    disagreements = 0
    total_bob_mismatch = 0
    bob_mismatch_stream = []
    final_decision = "continue"
    rounds_used = MAX_ROUNDS
    for i in range(MAX_ROUNDS):
        rec = run_protocol_round(i, mode, bob_sprt, charlie_sprt, noise_prob=noise, rng=rng)
        total_bob_mismatch += int(rec.bob_mismatch)
        bob_mismatch_stream.append(rec.bob_mismatch)
        if rec.disagreement:
            disagreements += 1
        if rec.symmetrized_decision in ("accept", "reject"):
            final_decision = rec.symmetrized_decision
            rounds_used = i + 1
            break
    elapsed = time.perf_counter() - start

    chi2 = chi_square_check(bob_mismatch_stream, p0)  # Phase 2: secondary cross-check, non-gating

    return {
        "mode": mode,
        "final_decision": final_decision,
        "rounds_used": rounds_used,
        "mismatch_rate": round(total_bob_mismatch / rounds_used, 4),
        "disagreements": disagreements,
        "latency_ms_per_round": round((elapsed / rounds_used) * 1000, 4),
        "total_runtime_s": round(elapsed, 4),
        "chi_square_secondary_check": chi2,
    }


def run_channel_tamper_experiment(rng) -> dict:
    """Phase 2: classical channel MAC demo, a separate detector for a
    separate threat (MITM tamper on the classical message), distinct from
    replay. Does not feed the security decision."""
    ch = ClassicalChannel()
    mac = WegmanCarterMAC(rng)
    t = ch.send(round_id=1, bits=(1, 0), basis="Z", nonce="n1")
    tag = mac.tag_for(t)
    import dataclasses
    tampered = dataclasses.replace(t, classical_bits=(0, 0))  # attacker flips a bit in transit
    detected = mac.verify(t, tag) and not mac.verify(tampered, tag)
    return {"mode": "classical_channel_tamper", "final_decision": "tamper_detected" if detected else "NOT DETECTED",
            "rounds_used": 1, "mismatch_rate": None, "disagreements": 0,
            "latency_ms_per_round": 0.0, "total_runtime_s": 0.0}


def run_replay_experiment() -> dict:
    channel = ClassicalChannel()
    honest = channel.send(round_id=5, bits=(1, 0), basis="Z", nonce="n5")
    accepted_honest = channel.receive(honest)
    replayed = channel.send(round_id=5, bits=(1, 0), basis="Z", nonce="n5")
    accepted_replay = channel.receive(replayed)
    detected = accepted_honest and not accepted_replay
    return {
        "mode": "replay",
        "final_decision": "reject" if detected else "accept",
        "rounds_used": 2,
        "mismatch_rate": None,
        "disagreements": 0,
        "latency_ms_per_round": 0.0,
        "total_runtime_s": 0.0,
        "note": "honest transcript accepted, replayed transcript rejected" if detected else "REPLAY NOT CAUGHT",
    }


def print_table(results: list):
    hdr = f"{'mode':<24}{'decision':<16}{'rounds':<8}{'mismatch':<10}{'disagree':<10}{'ms/round':<10}{'chi2 verdict':<14}"
    print(hdr)
    for r in results:
        mm = "-" if r["mismatch_rate"] is None else f"{r['mismatch_rate']:.4f}"
        chi = r.get("chi_square_secondary_check")
        chi_str = f"{chi['verdict']} (χ²={chi['chi2']})" if chi else "-"
        print(f"{r['mode']:<24}{r['final_decision']:<16}{r['rounds_used']:<8}{mm:<10}"
              f"{r['disagreements']:<10}{r['latency_ms_per_round']:<10.3f}{chi_str:<14}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["clean", "noisy", "intercept_resend", "impersonation",
                                            "cloning", "replay", "channel_tamper"])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save", type=str, default=None, help="path to save results as JSON")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    p0 = calibrate(rng)
    print(f"Calibration (real circuits, {EXPECTED_CHANNEL_NOISE:.0%} physical noise): p0 = {p0:.4f}\n")

    modes = ["clean", "noisy", "intercept_resend", "impersonation", "cloning"] if args.all else (
        [args.mode] if args.mode and args.mode not in ("replay", "channel_tamper") else []
    )
    results = [run_experiment(m, p0, rng) for m in modes]
    if args.all or args.mode == "replay":
        results.append(run_replay_experiment())
    if args.all or args.mode == "channel_tamper":
        results.append(run_channel_tamper_experiment(rng))

    print_table(results)

    epsilon = ATTACK_MARGIN / 2
    n_star = 200
    bound = hoeffding_false_accept_bound(n_star, epsilon)
    print(f"\nHoeffding bound @ n={n_star}, epsilon={epsilon:.3f}: P(false accept) <= {bound:.3e}")

    if args.all:
        s_honest = chsh_s_value(eve_intercept=False)
        s_attacked = chsh_s_value(eve_intercept=True)
        print(f"\nCHSH diagnostic (non-gating), honest: S={s_honest:.3f} "
              f"(classical bound 2, Tsirelson 2.828) | intercepted: S={s_attacked:.3f}")

    if args.save:
        Path(args.save).write_text(json.dumps({"p0": p0, "results": results,
                                                 "hoeffding_bound": bound, "n_star": n_star,
                                                 "epsilon": epsilon}, indent=2, default=str))
        print(f"\nSaved -> {args.save}")


if __name__ == "__main__":
    main()
