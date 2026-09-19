"""
detector.py, ENTANGLE

Primary, sole gating decision method: Wald's Sequential Probability Ratio
Test (SPRT) on the per-round mismatch stream. No AI/ML, this is a closed-
form sequential hypothesis test, unchanged since Wald (1945).

H0: honest channel, mismatch probability p0 (from calibration)
H1: attack in progress, mismatch probability p1 (from calibration + margin)
"""

import math
from dataclasses import dataclass, field


@dataclass
class SPRTResult:
    decision: str          # "continue" | "accept" | "reject"
    log_likelihood_ratio: float
    rounds_used: int


class SPRT:
    def __init__(self, p0: float, p1: float, alpha: float = 0.01, beta: float = 0.01):
        assert 0 < p0 < p1 < 1, "require p0 < p1 (honest rate must be below attack rate)"
        self.p0 = p0
        self.p1 = p1
        self.upper = math.log((1 - beta) / alpha)   # crossing => reject (attack)
        self.lower = math.log(beta / (1 - alpha))   # crossing => accept (honest)
        self.llr = 0.0
        self.n = 0

    def update(self, mismatch: bool) -> SPRTResult:
        x = 1 if mismatch else 0
        self.llr += x * math.log(self.p1 / self.p0) + (1 - x) * math.log(
            (1 - self.p1) / (1 - self.p0)
        )
        self.n += 1
        if self.llr >= self.upper:
            return SPRTResult("reject", self.llr, self.n)
        if self.llr <= self.lower:
            return SPRTResult("accept", self.llr, self.n)
        return SPRTResult("continue", self.llr, self.n)

    def reset(self):
        self.llr = 0.0
        self.n = 0


def calibrate_baseline(mismatches: list) -> float:
    """Honest-channel baseline mismatch rate p0, from a no-attack calibration run."""
    if not mismatches:
        return 1e-3
    rate = sum(mismatches) / len(mismatches)
    return max(rate, 1e-3)  # avoid log(0) in SPRT


def hoeffding_false_accept_bound(n: int, epsilon: float) -> float:
    """
    Upper bound on the probability that an attacker's induced disturbance
    stays under the detection margin for n rounds (Hoeffding's inequality).
    epsilon = gap between honest baseline and the attack-detection margin.
    """
    return math.exp(-2 * n * (epsilon ** 2))


# ---------------------------------------------------------------------------
# PHASE 2 (diagnostic / non-gating addition): chi-square secondary check
# ---------------------------------------------------------------------------
# Runs a chi-square goodness-of-fit test on the SAME mismatch data SPRT
# already consumed, as a robustness cross-check. It never feeds the
# accept/reject decision, SPRT remains the sole gating detector.

_CHI2_CRITICAL_DF1 = {0.01: 6.635, 0.05: 3.841}  # standard table values, df=1


def chi_square_check(mismatches: list, p0: float, alpha: float = 0.01) -> dict:
    n = len(mismatches)
    if n == 0:
        return {"chi2": 0.0, "critical": _CHI2_CRITICAL_DF1[alpha], "verdict": "accept", "n": 0}
    observed_mismatch = sum(1 for m in mismatches if m)
    observed_match = n - observed_mismatch
    expected_mismatch = max(n * p0, 1e-9)
    expected_match = max(n * (1 - p0), 1e-9)
    chi2 = ((observed_mismatch - expected_mismatch) ** 2 / expected_mismatch
            + (observed_match - expected_match) ** 2 / expected_match)
    critical = _CHI2_CRITICAL_DF1[alpha]
    verdict = "reject" if chi2 > critical else "accept"
    return {"chi2": round(chi2, 3), "critical": critical, "verdict": verdict, "n": n}
